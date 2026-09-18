from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.entities.client import Client
from app.domain.ports.client_repository import ClientRepository
from app.infrastructure.models.client import ClientModel


class SQLAlchemyClientRepository(ClientRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_domain(model: ClientModel) -> Client:
        return Client(
            id_cliente=model.id_cliente,
            tipo_cliente=model.tipo_cliente,
            nombre_razon_social=model.nombre_razon_social,
            nit_cc=model.nit_cc,
            nombre_contacto=model.nombre_contacto,
            telefono=model.telefono,
            email=model.email,
            direccion=model.direccion,
            ciudad=model.ciudad,
            observaciones=model.observaciones,
            estado=model.estado,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_id(self, client_id: UUID) -> Client | None:
        model = self.db.query(ClientModel).filter(ClientModel.id_cliente == client_id).first()
        return self._to_domain(model) if model else None

    def get_by_nit_cc(self, nit_cc: str) -> Client | None:
        model = self.db.query(ClientModel).filter(ClientModel.nit_cc == nit_cc).first()
        return self._to_domain(model) if model else None

    def list(
        self,
        search: str | None = None,
        estado: str | None = None,
        tipo: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Client], int]:
        query = self.db.query(ClientModel)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    ClientModel.nombre_razon_social.ilike(pattern),
                    ClientModel.nit_cc.ilike(pattern),
                    ClientModel.nombre_contacto.ilike(pattern),
                    ClientModel.ciudad.ilike(pattern),
                )
            )
        if estado is not None:
            query = query.filter(ClientModel.estado == estado)
        if tipo is not None:
            query = query.filter(ClientModel.tipo_cliente == tipo)
        total = query.count()
        models = query.order_by(ClientModel.created_at.desc()).offset(skip).limit(limit).all()
        return [self._to_domain(model) for model in models], total

    def create(
        self,
        tipo_cliente: str,
        nombre_razon_social: str,
        nit_cc: str,
        *,
        nombre_contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        observaciones: str | None = None,
        estado: str = "activo",
    ) -> Client:
        model = ClientModel(
            tipo_cliente=tipo_cliente,
            nombre_razon_social=nombre_razon_social,
            nit_cc=nit_cc,
            nombre_contacto=nombre_contacto,
            telefono=telefono,
            email=email,
            direccion=direccion,
            ciudad=ciudad,
            observaciones=observaciones,
            estado=estado,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(
        self,
        client_id: UUID,
        *,
        tipo_cliente: str | None = None,
        nombre_razon_social: str | None = None,
        nit_cc: str | None = None,
        nombre_contacto: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        ciudad: str | None = None,
        observaciones: str | None = None,
        estado: str | None = None,
    ) -> Client | None:
        model = self.db.query(ClientModel).filter(ClientModel.id_cliente == client_id).first()
        if model is None:
            return None
        if tipo_cliente is not None:
            model.tipo_cliente = tipo_cliente
        if nombre_razon_social is not None:
            model.nombre_razon_social = nombre_razon_social
        if nit_cc is not None:
            model.nit_cc = nit_cc
        if nombre_contacto is not None:
            model.nombre_contacto = nombre_contacto
        if telefono is not None:
            model.telefono = telefono
        if email is not None:
            model.email = email
        if direccion is not None:
            model.direccion = direccion
        if ciudad is not None:
            model.ciudad = ciudad
        if observaciones is not None:
            model.observaciones = observaciones
        if estado is not None:
            model.estado = estado
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)