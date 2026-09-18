from app.core.config import settings
from app.core.security import hash_password
from app.infrastructure.models.user import UserModel

ADMIN_NAME = "admin_user"


def seed_admin() -> None:
    """Garantiza que el usuario administrador bootstrap siempre exista."""
    from app.infrastructure.db import SessionLocal

    db = SessionLocal()
    try:
        exists = db.query(UserModel).filter(UserModel.email == settings.admin_email).first()
        if exists is not None:
            return

        db.add(
            UserModel(
                name=ADMIN_NAME,
                email=settings.admin_email,
                password=hash_password(settings.admin_password),
                rol="admin",
            )
        )
        db.commit()
    finally:
        db.close()


def seed_settings() -> None:
    """Garantiza que exista la fila única de system_settings con sus defaults."""
    from app.infrastructure.db import SessionLocal
    from app.infrastructure.models.system_settings import SystemSettingsModel

    db = SessionLocal()
    try:
        exists = db.query(SystemSettingsModel).filter(SystemSettingsModel.id == 1).first()
        if exists is not None:
            return
        db.add(SystemSettingsModel(id=1))
        db.commit()
    finally:
        db.close()