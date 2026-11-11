import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from backend.app.core.logging import logger

class DependencyGraphService:
    @staticmethod
    def build_project_graph(
        project_id: str,
        project_name: str,
        dependencies: List[Dict[str, Any]],
        package_vulns_map: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """
        Builds a NetworkX DiGraph from database dependencies records,
        calculates exact depths, detects circular dependencies, computes centralities,
        and generates React Flow formatted node and edge structures.
        """
        if package_vulns_map is None:
            package_vulns_map = {}

        G = nx.DiGraph()
        root_node_id = f"root_{project_id}"
        
        # Add Project Root Node
        G.add_node(
            root_node_id,
            node_type="project_root",
            name=project_name,
            version="1.0.0",
            is_direct=True,
            depth=0,
            is_vulnerable=False,
            highest_severity="NONE",
            vulnerabilities=[]
        )

        # Track added nodes to avoid duplicates
        added_nodes = set()

        # Step 1: Add all package nodes and connect edges
        for dep in dependencies:
            pkg_name = dep["package_name"]
            pkg_id = dep.get("package_id") or f"pkg_{pkg_name}"
            version = dep["resolved_version"]
            is_direct = dep.get("is_direct", False)
            parent_name = dep.get("parent_name")
            parent_id = dep.get("parent_package_id")

            vulns = package_vulns_map.get(pkg_name, [])
            highest_sev = "NONE"
            if vulns:
                severities = [v.get("severity", "LOW") for v in vulns]
                if "CRITICAL" in severities:
                    highest_sev = "CRITICAL"
                elif "HIGH" in severities:
                    highest_sev = "HIGH"
                elif "MEDIUM" in severities:
                    highest_sev = "MEDIUM"
                else:
                    highest_sev = "LOW"

            if pkg_name not in added_nodes:
                G.add_node(
                    pkg_name,
                    node_type="package",
                    package_id=pkg_id,
                    name=pkg_name,
                    version=version,
                    is_direct=is_direct,
                    depth=1 if is_direct else 2,
                    is_vulnerable=len(vulns) > 0,
                    highest_severity=highest_sev,
                    vulnerabilities=vulns
                )
                added_nodes.add(pkg_name)

            # Edge connections
            if is_direct or not parent_name:
                G.add_edge(root_node_id, pkg_name, edge_type="direct" if is_direct else "transitive")
            else:
                if parent_name in added_nodes:
                    G.add_edge(parent_name, pkg_name, edge_type="transitive")
                else:
                    # Parent hasn't been added yet, add temporary edge from root or add parent
                    G.add_edge(root_node_id, pkg_name, edge_type="transitive")

        # Step 2: Accurate depth calculation via NetworkX shortest paths
        max_depth = 0
        depth_distribution: Dict[int, int] = {}
        
        for node in G.nodes():
            if node == root_node_id:
                continue
            try:
                shortest_path = nx.shortest_path_length(G, source=root_node_id, target=node)
                G.nodes[node]["depth"] = shortest_path
                max_depth = max(max_depth, shortest_path)
                depth_distribution[shortest_path] = depth_distribution.get(shortest_path, 0) + 1
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                G.nodes[node]["depth"] = 2
                max_depth = max(max_depth, 2)
                depth_distribution[2] = depth_distribution.get(2, 0) + 1

        # Step 3: Circular dependency detection
        cycles = []
        try:
            raw_cycles = list(nx.simple_cycles(G))
            for cycle in raw_cycles:
                cycles.append(" -> ".join(cycle) + f" -> {cycle[0]}")
        except Exception as e:
            logger.warning(f"Cycle detection error: {e}")

        # Step 4: Centrality calculations
        in_degrees = dict(G.in_degree())
        out_degrees = dict(G.out_degree())
        betweenness = nx.betweenness_centrality(G)

        # Step 5: Generate formatted React Flow nodes with hierarchical coordinate layout
        nodes_by_depth: Dict[int, List[str]] = {}
        for node, data in G.nodes(data=True):
            d = data.get("depth", 0)
            nodes_by_depth.setdefault(d, []).append(node)

        rf_nodes = []
        x_spacing = 260
        y_spacing = 140

        for d, node_list in nodes_by_depth.items():
            count = len(node_list)
            start_x = -((count - 1) * x_spacing) / 2
            for idx, node_id in enumerate(node_list):
                data = G.nodes[node_id]
                pos_x = start_x + (idx * x_spacing)
                pos_y = d * y_spacing + 50

                rf_nodes.append({
                    "id": node_id,
                    "type": "customDependency",
                    "position": {"x": pos_x, "y": pos_y},
                    "data": {
                        "id": node_id,
                        "label": data.get("name"),
                        "version": data.get("version"),
                        "node_type": data.get("node_type"),
                        "is_direct": data.get("is_direct"),
                        "depth": data.get("depth"),
                        "is_vulnerable": data.get("is_vulnerable"),
                        "highest_severity": data.get("highest_severity"),
                        "vulnerabilities": data.get("vulnerabilities"),
                        "in_degree": in_degrees.get(node_id, 0),
                        "out_degree": out_degrees.get(node_id, 0),
                        "betweenness": round(betweenness.get(node_id, 0.0), 4)
                    }
                })

        # Step 6: Generate React Flow edges
        rf_edges = []
        edge_idx = 0
        for u, v, data in G.edges(data=True):
            edge_type = data.get("edge_type", "transitive")
            is_vuln_edge = G.nodes[v].get("is_vulnerable", False)
            rf_edges.append({
                "id": f"e_{edge_idx}_{u}_{v}",
                "source": u,
                "target": v,
                "animated": is_vuln_edge,
                "style": {
                    "stroke": "#EF4444" if is_vuln_edge else ("#06B6D4" if edge_type == "direct" else "#64748B"),
                    "strokeWidth": 2 if is_vuln_edge else 1.5
                },
                "data": {"edge_type": edge_type}
            })
            edge_idx += 1

        return {
            "root_node_id": root_node_id,
            "nodes": rf_nodes,
            "edges": rf_edges,
            "summary": {
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges(),
                "max_depth": max_depth,
                "direct_count": len([n for n, d in G.nodes(data=True) if d.get("is_direct") and n != root_node_id]),
                "transitive_count": len([n for n, d in G.nodes(data=True) if not d.get("is_direct") and n != root_node_id]),
                "circular_dependencies": cycles,
                "has_circular": len(cycles) > 0,
                "depth_distribution": depth_distribution
            }
        }
