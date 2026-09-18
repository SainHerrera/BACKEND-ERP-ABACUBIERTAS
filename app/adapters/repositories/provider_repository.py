from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.entities.provider import Provider
from app.domain.ports.provider_repository import ProviderRepository
from app.infrastructure.models.provider import ProviderModel


class SQLAlchemyProviderRepository(ProviderRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: ProviderModel) -> Provider:
        return Provider(
            id_proveedor=model.id_proveedor,
            nombre_empresa=model.nombre_empresa,
            nit=model.nit,
            contacto=model.contacto,
            telefono=model.telefono,
            email=model.email,
            direccion=model.direccion,
            ciudad=model.ciudad,
            categoria_material=model.categoria_material,
            condiciones_pago=model.condiciones_pago,
            observaciones=model.observaciones,
            estado=model.estado,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_id(self, provider_id: UUID) -> Provider | None:
        model = self.db.query(ProviderModel).filter(ProviderModel.id_proveedor == provider_id).first()
        return self._to_domain(model) if model else None

    def get_by_nit(self, nit: str) -> Provider | None:
        model = self.db.query(ProviderModel).filter(ProviderModel.nit == nit).first()
        return self._to_domain(model) if model else None

    def list(
        self, search: str | None = None, skip: int = 0, limit: int = 50
    ) -> tuple[list[Provider], int]:
        query = self.db.query(ProviderModel)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    ProviderModel.nombre_empresa.ilike(pattern),
                    ProviderModel.nit.ilike(pattern),
                    ProviderModel.contacto.ilike(pattern),
                    ProviderModel.ciudad.ilike(pattern),
                )
            )
        total = query.count()
        models = query.order_by(ProviderModel.created_at.desc()).offset(skip).limit(limit).all()
        return [self._to_domain(model) for model in models], total

    def create(
        self,
        nombre_empresa: str,
        nit: str,
        *,
        contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        categoria_material: str = "general",
        condiciones_pago: str | None = None,
        observaciones: str | None = None,
        estado: str = "activo",
    ) -> Provider:
        model = ProviderModel(
            nombre_empresa=nombre_empresa,
            nit=nit,
            contacto=contacto,
            telefono=telefono,
            email=email,
            direccion=direccion,
            ciudad=ciudad,
            categoria_material=categoria_material,
            condiciones_pago=condiciones_pago,
            observaciones=observaciones,
            estado=estado,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(
        self,
        provider_id: UUID,
        *,
        nombre_empresa: str | None = None,
        nit: str | None = None,
        contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        categoria_material: str | None = None,
        condiciones_pago: str | None = None,
        observaciones: str | None = None,
        estado: str | None = None,
    ) -> Provider | None:
        model = self.db.query(ProviderModel).filter(ProviderModel.id_proveedor == provider_id).first()
        if model is None:
            return None
        if nombre_empresa is not None:
            model.nombre_empresa = nombre_empresa
        if nit is not None:
            model.nit = nit
        if contacto is not None:
            model.contacto = contacto
        if telefono is not None:
            model.telefono = telefono
        if email is not None:
            model.email = email
        if direccion is not None:
            model.direccion = direccion
        if ciudad is not None:
            model.ciudad = ciudad
        if categoria_material is not None:
            model.categoria_material = categoria_material
        if condiciones_pago is not None:
            model.condiciones_pago = condiciones_pago
        if observaciones is not None:
            model.observaciones = observaciones
        if estado is not None:
            model.estado = estado
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)