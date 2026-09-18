from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.entities.audit_log_entry import AuditLogEntry
from app.domain.ports.audit_log_repository import AuditLogRepository
from app.infrastructure.models.audit_log import AuditLogModel


class SQLAlchemyAuditLogRepository(AuditLogRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: AuditLogModel) -> AuditLogEntry:
        return AuditLogEntry(
            id=model.id,
            fecha=model.fecha,
            id_usuario=model.id_usuario,
            nombre_usuario=model.nombre_usuario,
            email_usuario=model.email_usuario,
            rol_usuario=model.rol_usuario,
            accion=model.accion,
            detalle=model.detalle,
        )

    def create(
        self,
        *,
        fecha: datetime | None,
        id_usuario: UUID | None,
        nombre_usuario: str | None,
        email_usuario: str | None,
        rol_usuario: str | None,
        accion: str,
        detalle: str,
    ) -> AuditLogEntry:
        model = AuditLogModel(
            fecha=fecha,
            id_usuario=id_usuario,
            nombre_usuario=nombre_usuario,
            email_usuario=email_usuario,
            rol_usuario=rol_usuario,
            accion=accion,
            detalle=detalle,
        )
        self.db.add(model)
        self.db.flush()
        return self._to_domain(model)

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        usuario: str | None = None,
        accion: str | None = None,
    ) -> tuple[list[AuditLogEntry], int]:
        query = self.db.query(AuditLogModel)
        if usuario:
            pattern = f"%{usuario}%"
            query = query.filter(
                or_(
                    AuditLogModel.nombre_usuario.ilike(pattern),
                    AuditLogModel.email_usuario.ilike(pattern),
                )
            )
        if accion:
            query = query.filter(AuditLogModel.accion == accion)
        total = query.count()
        models = (
            query.order_by(AuditLogModel.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models], total

    def clear(self) -> None:
        self.db.query(AuditLogModel).delete()
        self.db.flush()