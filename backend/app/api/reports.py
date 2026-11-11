from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.entities import Project, User
from backend.app.core.security import get_current_user
from backend.app.core.logging import log_activity
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Security Reports"])

@router.get("/{project_id}", response_class=HTMLResponse)
def get_html_report(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    html_content = ReportService.generate_html_report(project_id, db)

    log_activity(
        db,
        action="REPORT_GENERATE_HTML",
        entity_type="REPORT",
        entity_id=project_id,
        user_id=current_user.id,
        organization_id=project.organization_id,
        details=f"Viewed HTML executive report for '{project.name}'"
    )

    return HTMLResponse(content=html_content)

@router.get("/{project_id}/export")
def export_report(
    project_id: str,
    format: str = Query("csv", pattern="^(csv|html)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if format == "csv":
        csv_data = ReportService.generate_csv_report(project_id, db)
        filename = f"dependencyx_audit_{project.name.lower().replace(' ', '_')}.csv"
        
        log_activity(
            db,
            action="REPORT_EXPORT_CSV",
            entity_type="REPORT",
            entity_id=project_id,
            user_id=current_user.id,
            organization_id=project.organization_id,
            details=f"Exported CSV security audit report for '{project.name}'"
        )

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        html_data = ReportService.generate_html_report(project_id, db)
        filename = f"dependencyx_report_{project.name.lower().replace(' ', '_')}.html"
        return Response(
            content=html_data,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
