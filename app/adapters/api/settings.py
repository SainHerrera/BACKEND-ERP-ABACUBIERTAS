from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.adapters.api.audit import auditar
from app.adapters.deps import get_current_user, require_roles
from app.adapters.repositories.product_repository import SQLAlchemyProductRepository
from app.adapters.repositories.provider_repository import SQLAlchemyProviderRepository
from app.adapters.repositories.system_settings_repository import (
    SQLAlchemySystemSettingsRepository,
)
from app.adapters.schemas import CatalogLoadRead, SettingsRead, SettingsUpdate
from app.application.services.catalog_service import CatalogService
from app.application.services.system_settings_service import SystemSettingsService
from app.domain.entities.system_settings import SystemSettings
from app.domain.entities.user import User
from app.infrastructure.db import get_db

router = APIRouter(prefix="/settings", tags=["settings"])

WRITE_ROLES = ("admin",)


def _build_service(db: Session) -> SystemSettingsService:
    return SystemSettingsService(SQLAlchemySystemSettingsRepository(db))


def _to_read(s: SystemSettings) -> SettingsRead:
    return SettingsRead(
        stock_minimo_default=s.stock_minimo_default,
        margen_utilidad_default=s.margen_utilidad_default,
        catalogo_inicial_cargado=s.catalogo_inicial_cargado,
        aprobacion_oc_habilitada=s.aprobacion_oc_habilitada,
        aprobacion_oc_monto_minimo=s.aprobacion_oc_monto_minimo,
        updated_at=s.updated_at,
    )


@router.get("", response_model=SettingsRead)
def get_settings(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SettingsRead:
    return _to_read(_build_service(db).get())


@router.patch("", response_model=SettingsRead)
def update_settings(
    data: SettingsUpdate,
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> SettingsRead:
    payload = data.model_dump(exclude_unset=True)
    result = _to_read(_build_service(db).update(**payload))
    auditar(db, current_user, "settings_updated", "Parámetros del sistema actualizados")
    return result


@router.post("/reset", response_model=SettingsRead)
def reset_settings(
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> SettingsRead:
    result = _to_read(_build_service(db).reset())
    auditar(db, current_user, "settings_reset", "Parámetros del sistema restablecidos")
    return result


@router.post("/load-catalog", response_model=CatalogLoadRead)
def load_catalog(
    current_user: User = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> CatalogLoadRead:
    """Carga el catálogo inicial (productos/proveedores) si las tablas están vacías."""
    service = CatalogService(
        providers=SQLAlchemyProviderRepository(db),
        products=SQLAlchemyProductRepository(db),
        settings=SQLAlchemySystemSettingsRepository(db),
    )
    result = service.load()
    auditar(
        db,
        current_user,
        "catalog_loaded",
        f"Catálogo inicial cargado ({result['products']} productos, {result['providers']} proveedores)",
    )
    return CatalogLoadRead(**result)