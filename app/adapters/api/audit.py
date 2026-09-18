from sqlalchemy.orm import Session

from app.adapters.repositories.audit_log_repository import SQLAlchemyAuditLogRepository
from app.application.services.audit_log_service import AuditLogService
from app.domain.entities.user import User


def auditar(db: Session, actor: User | None, accion: str, detalle: str) -> None:
    """Registra una entrada de auditoria en transacción propia sin romper el flujo."""
    try:
        service = AuditLogService(SQLAlchemyAuditLogRepository(db))
        service.record(
            accion=accion,
            detalle=detalle,
            id_usuario=actor.id if actor else None,
            nombre_usuario=actor.name if actor else None,
            email_usuario=actor.email if actor else None,
            rol_usuario=actor.rol if actor else None,
        )
        db.commit()
    except Exception:
        db.rollback()