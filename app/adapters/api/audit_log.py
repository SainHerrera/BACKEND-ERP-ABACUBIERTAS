from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.adapters.deps import require_admin, require_roles
from app.adapters.repositories.audit_log_repository import SQLAlchemyAuditLogRepository
from app.adapters.schemas import AuditLogListResponse, AuditLogRead
from app.application.services.audit_log_service import AuditLogService
from app.domain.entities.user import User
from app.infrastructure.db import get_db

router = APIRouter(prefix="/audit-log", tags=["audit-log"])

READ_ROLES = ("admin", "gerencia")


def _build_service(db: Session) -> AuditLogService:
    return AuditLogService(SQLAlchemyAuditLogRepository(db))


def _to_read(entry) -> AuditLogRead:
    return AuditLogRead(
        id=entry.id,
        fecha=entry.fecha,
        id_usuario=entry.id_usuario,
        nombre_usuario=entry.nombre_usuario,
        email_usuario=entry.email_usuario,
        rol_usuario=entry.rol_usuario,
        accion=entry.accion,
        detalle=entry.detalle,
    )


@router.get("", response_model=AuditLogListResponse)
def list_audit_log(
    usuario: str | None = Query(default=None, description="Filtra por nombre o email"),
    accion: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    _current_user: User = Depends(require_roles(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    items, total = _build_service(db).list(
        skip=skip, limit=limit, usuario=usuario, accion=accion
    )
    return AuditLogListResponse(items=[_to_read(e) for e in items], total=total)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_audit_log(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    service = _build_service(db)
    service.clear()
    db.commit()