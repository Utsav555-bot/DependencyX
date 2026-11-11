import pytest
from backend.app.graph_engine.graph_service import DependencyGraphService

def test_build_project_graph_and_depths():
    dependencies = [
        {"package_name": "express", "resolved_version": "4.18.2", "is_direct": True, "parent_name": None, "depth": 1},
        {"package_name": "cookie", "resolved_version": "0.5.0", "is_direct": False, "parent_name": "express", "depth": 2},
        {"package_name": "deep-lib", "resolved_version": "1.0.0", "is_direct": False, "parent_name": "cookie", "depth": 3}
    ]

    result = DependencyGraphService.build_project_graph(
        project_id="prj_1",
        project_name="Express App",
        dependencies=dependencies
    )

    assert result["summary"]["total_nodes"] == 4  # 1 root + 3 packages
    assert result["summary"]["max_depth"] == 3
    assert result["summary"]["direct_count"] == 1
    assert result["summary"]["transitive_count"] == 2
    assert result["summary"]["has_circular"] is False

    # Check node positions and data
    cookie_node = next(n for n in result["nodes"] if n["id"] == "cookie")
    assert cookie_node["data"]["depth"] == 2
    assert cookie_node["data"]["is_direct"] is False

def test_circular_dependency_detection():
    # Artificially create circular dependency: A -> B -> A
    dependencies = [
        {"package_name": "pkgA", "resolved_version": "1.0.0", "is_direct": True, "parent_name": None, "depth": 1},
        {"package_name": "pkgB", "resolved_version": "1.0.0", "is_direct": False, "parent_name": "pkgA", "depth": 2},
        {"package_name": "pkgA", "resolved_version": "1.0.0", "is_direct": False, "parent_name": "pkgB", "depth": 3}
    ]

    result = DependencyGraphService.build_project_graph(
        project_id="prj_cycle",
        project_name="Cyclic Project",
        dependencies=dependencies
    )

    assert result["summary"]["has_circular"] is True
    assert len(result["summary"]["circular_dependencies"]) > 0
