from uuid import UUID

from app.domain.entities.client import Client
from app.domain.exceptions import (
    ClientNotFound,
    DuplicateClientNitCc,
)
from app.domain.ports.client_repository import ClientRepository


class ClientService:
    def __init__(self, clients: ClientRepository):
        self.clients = clients

    def create(
        self,
        tipo_cliente: str,
        nombre_razon_social: str,
        nit_cc: str,
        **kwargs,
    ) -> Client:
        if self.clients.get_by_nit_cc(nit_cc) is not None:
            raise DuplicateClientNitCc("Ya existe un cliente registrado con el NIT/CC")
        return self.clients.create(
            tipo_cliente=tipo_cliente,
            nombre_razon_social=nombre_razon_social,
            nit_cc=nit_cc,
            **kwargs,
        )

    def list(
        self,
        search: str | None = None,
        estado: str | None = None,
        tipo: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Client], int]:
        return self.clients.list(search=search, estado=estado, tipo=tipo, skip=skip, limit=limit)

    def get(self, client_id: UUID) -> Client:
        client = self.clients.get_by_id(client_id)
        if client is None:
            raise ClientNotFound("Cliente no encontrado")
        return client

    def update(self, client_id: UUID, **fields) -> Client:
        if fields.get("nit_cc") is not None:
            existing = self.clients.get_by_nit_cc(fields["nit_cc"])
            if existing is not None and existing.id_cliente != client_id:
                raise DuplicateClientNitCc("Ya existe un cliente registrado con el NIT/CC")
        client = self.clients.update(client_id, **fields)
        if client is None:
            raise ClientNotFound("Cliente no encontrado")
        return client

    def deactivate(self, client_id: UUID) -> Client:
        return self.update(client_id, estado="inactivo")