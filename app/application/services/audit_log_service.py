from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.audit_log_entry import AuditLogEntry
from app.domain.ports.audit_log_repository import AuditLogRepository

VALID_ACCIONES = {
    "login",
    "logout",
    "user_created",
    "user_updated",
    "user_deactivated",
    "user_activated",
    "role_changed",
    "settings_updated",
    "settings_reset",
    "catalog_loaded",
    "purchase_order_created",
    "purchase_order_received",
    "purchase_order_in_transit",
    "purchase_order_pending_approval",
    "purchase_order_approved",
    "purchase_order_rejected",
    "provider_quotation_created",
    "provider_quotation_selected",
    "sale_dispatched",
    "stock_request_created",
    "stock_request_updated",
}


class AuditLogService:
    def __init__(self, logs: AuditLogRepository):
        self.logs = logs

    def record(
        self,
        *,
        accion: str,
        detalle: str,
        id_usuario: UUID | None = None,
        nombre_usuario: str | None = None,
        email_usuario: str | None = None,
        rol_usuario: str | None = None,
    ) -> AuditLogEntry:
        # Acciones desconocidas no bloquean el registro de operaciones significativas.
        entry = self.logs.create(
            fecha=datetime.now(),
            id_usuario=id_usuario,
            nombre_usuario=nombre_usuario,
            email_usuario=email_usuario,
            rol_usuario=rol_usuario,
            accion=accion,
            detalle=detalle,
        )
        return entry

    def list(
        self,
        skip: int = 0,
        limit: int = 50,
        usuario: str | None = None,
        accion: str | None = None,
    ) -> tuple[list[AuditLogEntry], int]:
        return self.logs.list(
            skip=skip, limit=limit, usuario=usuario, accion=accion
        )

    def clear(self) -> None:
        self.logs.clear()