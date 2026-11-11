from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Project, OrganizationMember, Dependency, ScanHistory, RiskAssessment, User
from backend.app.schemas.all_schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.app.core.security import get_current_user
from backend.app.core.logging import log_activity

router = APIRouter(prefix="/projects", tags=["Project Management"])

def _get_user_org_id(current_user: User, db: Session) -> str:
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=400, detail="User is not affiliated with any organization.")
    return membership.organization_id

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org_id = _get_user_org_id(current_user, db)
    projects = db.query(Project).filter(Project.organization_id == org_id).all()

    results = []
    for p in projects:
        # Aggregated stats
        total_deps = db.query(Dependency).filter(Dependency.project_id == p.id).count()
        latest_scan = (
            db.query(ScanHistory)
            .filter(ScanHistory.project_id == p.id)
            .order_by(ScanHistory.created_at.desc())
            .first()
        )
        latest_risk = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.project_id == p.id)
            .order_by(RiskAssessment.created_at.desc())
            .first()
        )

        results.append(ProjectResponse(
            id=p.id,
            organization_id=p.organization_id,
            name=p.name,
            description=p.description,
            ecosystem=p.ecosystem,
            repository_url=p.repository_url,
            manifest_blob_path=p.manifest_blob_path,
            created_by=p.created_by,
            created_at=p.created_at,
            updated_at=p.updated_at,
            total_dependencies=total_deps,
            vulnerable_packages_count=latest_scan.vulnerable_packages_count if latest_scan else 0,
            risk_score=latest_risk.overall_score if latest_risk else 0.0,
            risk_level=latest_risk.risk_level if latest_risk else "LOW"
        ))

    return results

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org_id = _get_user_org_id(current_user, db)

    existing = db.query(Project).filter(
        Project.organization_id == org_id,
        Project.name == project_in.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A project named '{project_in.name}' already exists in your organization."
        )

    project = Project(
        organization_id=org_id,
        name=project_in.name,
        description=project_in.description,
        ecosystem=project_in.ecosystem or "npm",
        repository_url=project_in.repository_url,
        created_by=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    log_activity(
        db,
        action="PROJECT_CREATE",
        entity_type="PROJECT",
        entity_id=project.id,
        user_id=current_user.id,
        organization_id=org_id,
        details=f"Created project '{project.name}'"
    )

    return ProjectResponse(
        id=project.id,
        organization_id=project.organization_id,
        name=project.name,
        description=project.description,
        ecosystem=project.ecosystem,
        repository_url=project.repository_url,
        manifest_blob_path=project.manifest_blob_path,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        total_dependencies=0,
        vulnerable_packages_count=0,
        risk_score=0.0,
        risk_level="LOW"
    )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org_id = _get_user_org_id(current_user, db)
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == org_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    total_deps = db.query(Dependency).filter(Dependency.project_id == project.id).count()
    latest_scan = (
        db.query(ScanHistory)
        .filter(ScanHistory.project_id == project.id)
        .order_by(ScanHistory.created_at.desc())
        .first()
    )
    latest_risk = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.project_id == project.id)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )

    return ProjectResponse(
        id=project.id,
        organization_id=project.organization_id,
        name=project.name,
        description=project.description,
        ecosystem=project.ecosystem,
        repository_url=project.repository_url,
        manifest_blob_path=project.manifest_blob_path,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        total_dependencies=total_deps,
        vulnerable_packages_count=latest_scan.vulnerable_packages_count if latest_scan else 0,
        risk_score=latest_risk.overall_score if latest_risk else 0.0,
        risk_level=latest_risk.risk_level if latest_risk else "LOW"
    )

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org_id = _get_user_org_id(current_user, db)
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == org_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Authorization: Admins can edit any project; Developers can only edit projects they created
    if current_user.role != "admin" and project.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied to modify this project.")

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.repository_url is not None:
        project.repository_url = project_in.repository_url

    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)

    log_activity(
        db,
        action="PROJECT_UPDATE",
        entity_type="PROJECT",
        entity_id=project.id,
        user_id=current_user.id,
        organization_id=org_id,
        details=f"Updated project '{project.name}'"
    )

    return get_project(project_id, current_user, db)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org_id = _get_user_org_id(current_user, db)
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == org_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # RBAC: Admin can delete any project in their organization; Developer can only delete their own
    if current_user.role != "admin" and project.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied to delete this project.")

    db.delete(project)
    db.commit()

    log_activity(
        db,
        action="PROJECT_DELETE",
        entity_type="PROJECT",
        entity_id=project_id,
        user_id=current_user.id,
        organization_id=org_id,
        details=f"Deleted project '{project.name}'"
    )
    return None
