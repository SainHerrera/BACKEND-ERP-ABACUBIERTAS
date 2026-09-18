import uuid
from datetime import datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

VALID_ROLES = {"admin", "ventas", "compras", "bodega", "gerencia"}


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=26)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    rol: str = "ventas"

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, value: str) -> str:
        if value not in VALID_ROLES:
            raise ValueError(f"Rol inválido. Permitidos: {', '.join(sorted(VALID_ROLES))}")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    rol: str | None = None
    status: bool | None = None

    @field_validator("name")
    @classmethod
    def validar_name(cls, value: str | None) -> str | None:
        if value is not None:
            if len(value) < 2 or len(value) > 26:
                raise ValueError("El nombre debe tener entre 2 y 26 caracteres")
        return value

    @field_validator("password")
    @classmethod
    def validar_password(cls, value: str | None) -> str | None:
        if value is not None:
            if len(value) < 8 or len(value) > 128:
                raise ValueError("La contraseña debe tener entre 8 y 128 caracteres")
        return value

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_ROLES:
            raise ValueError(f"Rol inválido. Permitidos: {', '.join(sorted(VALID_ROLES))}")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    rol: str
    status: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int


# --------------------------------------------------------------------------
# Providers
# --------------------------------------------------------------------------

class ProviderCreate(BaseModel):
    nombre_empresa: str = Field(min_length=2, max_length=120)
    nit: str = Field(min_length=3, max_length=30)
    contacto: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = None
    categoria_material: str = Field(default="general", max_length=50)
    condiciones_pago: str | None = Field(default=None, max_length=120)
    observaciones: str | None = None
    estado: Literal["activo", "inactivo", "preferente"] = "activo"


class ProviderUpdate(BaseModel):
    nombre_empresa: str | None = Field(default=None, min_length=2, max_length=120)
    nit: str | None = Field(default=None, min_length=3, max_length=30)
    contacto: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = None
    categoria_material: str | None = Field(default=None, max_length=50)
    condiciones_pago: str | None = Field(default=None, max_length=120)
    observaciones: str | None = None
    estado: Literal["activo", "inactivo", "preferente"] | None = None


class ProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_proveedor: uuid.UUID
    nombre_empresa: str
    nit: str
    contacto: str | None
    telefono: str | None
    email: str | None
    direccion: str | None
    ciudad: str | None
    categoria_material: str
    condiciones_pago: str | None
    observaciones: str | None
    estado: str
    activo: bool
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Products
# --------------------------------------------------------------------------

class ProductCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = None
    unidad_medida: str = Field(default="unidad", max_length=30)
    precio_unitario: float = Field(default=0, ge=0)
    stock_inicial: int | None = Field(default=None, ge=0)
    stock_minimo: int = Field(default=15, ge=0)
    id_proveedor: uuid.UUID | None = None


class ProductUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    descripcion: str | None = None
    unidad_medida: str | None = Field(default=None, max_length=30)
    precio_unitario: float | None = Field(default=None, ge=0)
    stock_minimo: int | None = Field(default=None, ge=0)
    id_proveedor: uuid.UUID | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_producto: uuid.UUID
    nombre: str
    descripcion: str | None
    unidad_medida: str
    precio_unitario: float
    stock_actual: int
    stock_minimo: int
    id_proveedor: uuid.UUID | None
    nombre_proveedor: str | None
    activo: bool
    status: str
    low_stock: bool
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------

class ClientCreate(BaseModel):
    tipo_cliente: Literal["empresa", "persona_natural"] = "empresa"
    nombre_razon_social: str = Field(min_length=2, max_length=150)
    nit_cc: str = Field(min_length=3, max_length=30)
    nombre_contacto: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = None
    observaciones: str | None = None
    estado: Literal["activo", "inactivo", "prospecto", "frecuente", "corporativo"] = "activo"


class ClientUpdate(BaseModel):
    tipo_cliente: Literal["empresa", "persona_natural"] | None = None
    nombre_razon_social: str | None = Field(default=None, min_length=2, max_length=150)
    nit_cc: str | None = Field(default=None, min_length=3, max_length=30)
    nombre_contacto: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = None
    observaciones: str | None = None
    estado: Literal["activo", "inactivo", "prospecto", "frecuente", "corporativo"] | None = None


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cliente: uuid.UUID
    tipo_cliente: str
    nombre_razon_social: str
    nit_cc: str
    nombre_contacto: str | None
    telefono: str | None
    email: str | None
    direccion: str | None
    ciudad: str | None
    observaciones: str | None
    estado: str
    activo: bool
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Movements
# --------------------------------------------------------------------------

class MovementCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)
    reference: str | None = None
    note: str | None = None
    fecha: datetime | None = None


class MovementEntryCreate(MovementCreate):
    pass


class MovementOutputCreate(MovementCreate):
    pass


class MovementAdjustmentCreate(MovementCreate):
    pass


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_movimiento: uuid.UUID
    id_producto: uuid.UUID
    tipo: str
    cantidad: int
    referencia: str | None
    id_usuario: uuid.UUID | None
    fecha: datetime
    nota: str | None


# --------------------------------------------------------------------------
# Quotations
# --------------------------------------------------------------------------

VALID_ESTADOS_COTIZACION = ("borrador", "enviada", "aprobada", "rechazada", "vencida")


class QuotationDetailCreate(BaseModel):
    id_producto: uuid.UUID
    descripcion: str | None = None
    cantidad: int = Field(gt=0)
    # 0/omitido -> el backend aplica el margen de utilidad sobre el precio del producto.
    precio_unitario: Decimal = Field(default=Decimal("0"), ge=0)
    descuento: Decimal = Field(default=Decimal("0"), ge=0)


class QuotationCreate(BaseModel):
    id_cliente: uuid.UUID
    fecha_vencimiento: datetime | None = None
    descuento: Decimal = Field(default=Decimal("0"), ge=0)
    observaciones: str | None = None
    detalles: list[QuotationDetailCreate] = Field(min_length=1)


class QuotationUpdate(BaseModel):
    id_cliente: uuid.UUID | None = None
    fecha_vencimiento: datetime | None = None
    descuento: Decimal | None = Field(default=None, ge=0)
    observaciones: str | None = None
    detalles: list[QuotationDetailCreate] | None = None


class QuotationEstadoUpdate(BaseModel):
    estado: Literal["borrador", "enviada", "aprobada", "rechazada", "vencida"]


class QuotationDetailRead(BaseModel):
    # id_detalle es la posición (1-based) del detalle dentro de la cotización,
    # para respetar el tipo `QuotationDetail` del frontend.
    id_detalle: int
    id_producto: uuid.UUID
    descripcion: str | None
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal
    subtotal: Decimal


class QuotationRead(BaseModel):
    id_cotizacion: uuid.UUID
    numero_consecutivo: str
    id_cliente: uuid.UUID
    nombre_cliente: str | None
    id_usuario: uuid.UUID | None
    fecha_emision: datetime
    fecha_vencimiento: datetime | None
    estado: str
    subtotal: Decimal
    impuestos: Decimal
    descuento: Decimal
    total: Decimal
    observaciones: str | None
    detalles: list[QuotationDetailRead]
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# System settings
# --------------------------------------------------------------------------

class SettingsUpdate(BaseModel):
    stock_minimo_default: int | None = Field(default=None, ge=0)
    margen_utilidad_default: int | None = Field(default=None, ge=0, le=100)
    catalogo_inicial_cargado: bool | None = None
    aprobacion_oc_habilitada: bool | None = None
    aprobacion_oc_monto_minimo: Decimal | None = Field(default=None, ge=0)


class SettingsRead(BaseModel):
    stock_minimo_default: int
    margen_utilidad_default: int
    catalogo_inicial_cargado: bool
    aprobacion_oc_habilitada: bool
    aprobacion_oc_monto_minimo: Decimal
    updated_at: datetime | None


class CatalogLoadRead(BaseModel):
    products: int
    providers: int


# --------------------------------------------------------------------------
# Sales
# --------------------------------------------------------------------------

VALID_ESTADOS_SALE = ("pendiente", "en_proceso", "entregada", "cancelada")


class SaleDetailCreate(BaseModel):
    id_producto: uuid.UUID
    descripcion: str | None = None
    cantidad: int = Field(gt=0)
    # 0/omitido -> el backend usa el precio del producto.
    precio_unitario: Decimal = Field(default=Decimal("0"), ge=0)
    descuento: Decimal = Field(default=Decimal("0"), ge=0)


class SaleCreate(BaseModel):
    id_cliente: uuid.UUID
    id_cotizacion: uuid.UUID | None = None
    observaciones: str | None = None
    detalles: list[SaleDetailCreate] = Field(min_length=1)


class SaleUpdate(BaseModel):
    estado: Literal["pendiente", "en_proceso", "entregada", "cancelada"] | None = None
    observaciones: str | None = None


class SaleDetailRead(BaseModel):
    # id_detalle es la posición (1-based) del detalle dentro del pedido,
    # para respetar el tipo `SaleDetail` del frontend.
    id_detalle: int
    id_producto: uuid.UUID
    descripcion: str | None
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal
    subtotal: Decimal


class SaleRead(BaseModel):
    id_orden_venta: uuid.UUID
    numero_orden: str
    id_cliente: uuid.UUID
    nombre_cliente: str | None
    id_cotizacion: uuid.UUID | None
    id_usuario: uuid.UUID | None
    fecha_venta: datetime
    estado: str
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal
    observaciones: str | None
    detalles: list[SaleDetailRead]
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Purchase Orders
# --------------------------------------------------------------------------

VALID_ESTADOS_PO = (
    "pendiente_aprobacion",
    "enviada",
    "en_transito",
    "recibida",
    "rechazada",
)


class PurchaseOrderDetailCreate(BaseModel):
    id_producto: uuid.UUID
    descripcion: str | None = None
    cantidad_ordenada: int = Field(gt=0)
    precio_unitario: Decimal = Field(gt=0)
    tiempo_entrega_dias: int | None = Field(default=None, ge=0)


class PurchaseOrderCreate(BaseModel):
    id_proveedor: uuid.UUID
    fecha_emision: datetime | None = None
    observaciones: str | None = None
    id_solicitud: uuid.UUID | None = None
    numero_solicitud: str | None = None
    id_cotizacion: uuid.UUID | None = None
    detalles: list[PurchaseOrderDetailCreate] = Field(min_length=1)


class PurchaseOrderDetailRead(BaseModel):
    # id_detalle es la posición (1-based) del detalle dentro de la orden,
    # para respetar el tipo `PurchaseOrderDetail` del frontend.
    id_detalle: int
    id_producto: uuid.UUID
    descripcion: str | None
    cantidad_ordenada: int
    cantidad_recibida: int
    precio_unitario: Decimal
    tiempo_entrega_dias: int | None


class PurchaseOrderRead(BaseModel):
    id_orden_compra: uuid.UUID
    numero_oc: str
    id_proveedor: uuid.UUID
    nombre_proveedor: str | None
    fecha_emision: datetime
    estado: str
    observaciones: str | None
    id_solicitud: uuid.UUID | None
    numero_solicitud: str | None
    id_cotizacion: uuid.UUID | None
    total: Decimal
    detalles: list[PurchaseOrderDetailRead]
    created_at: datetime
    updated_at: datetime


class ReceivePoCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)
    fecha: datetime | None = None
    note: str | None = None


class ApprovePoUpdate(BaseModel):
    aprobar: bool


# --------------------------------------------------------------------------
# Stock Requests
# --------------------------------------------------------------------------

VALID_ESTADOS_STOCK_REQUEST = ("pendiente", "aprobada", "atendida", "rechazada")


class StockRequestCreate(BaseModel):
    id_producto: uuid.UUID
    cantidad_sugerida: int = Field(gt=0)
    observaciones: str | None = None


class StockRequestStatusUpdate(BaseModel):
    estado: Literal["pendiente", "aprobada", "atendida", "rechazada"]


class StockRequestRead(BaseModel):
    id_solicitud: uuid.UUID
    numero_solicitud: str
    id_producto: uuid.UUID
    descripcion: str
    cantidad_sugerida: int
    stock_actual: int
    stock_minimo: int
    estado: str
    fecha: datetime
    id_usuario: uuid.UUID | None
    nombre_usuario: str | None
    observaciones: str | None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Provider Quotations
# --------------------------------------------------------------------------

class ProviderQuotationCreate(BaseModel):
    id_solicitud: uuid.UUID
    id_producto: uuid.UUID
    id_proveedor: uuid.UUID
    precio_unitario: Decimal = Field(gt=0)
    tiempo_entrega_dias: int = Field(gt=0)
    condiciones: str | None = None


class ProviderQuotationSelectUpdate(BaseModel):
    seleccionada: bool = True


class ProviderQuotationRead(BaseModel):
    id_cotizacion: uuid.UUID
    numero_cotizacion: str
    id_solicitud: uuid.UUID
    id_producto: uuid.UUID
    id_proveedor: uuid.UUID
    nombre_proveedor: str | None
    precio_unitario: Decimal
    tiempo_entrega_dias: int
    condiciones: str | None
    fecha: datetime
    seleccionada: bool
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------

class ReportKpis(BaseModel):
    ventasDelMes: float
    totalVentas: float
    cotizacionesPendientes: int
    stockCritico: int
    comprasPendientes: int
    aprobacionesPendientes: int


class ReportSalesBySellerItem(BaseModel):
    id_usuario: str
    vendedor: str
    total: float
    ventas: int


class ReportSalesMonthlyItem(BaseModel):
    mes: str
    total: float


class ReportInventoryProduct(BaseModel):
    id_producto: uuid.UUID
    nombre: str
    stock_actual: int
    precio_unitario: float
    valor: float


class ReportInventoryValuation(BaseModel):
    valorTotal: float
    porProducto: list[ReportInventoryProduct]


class ReportProviderExpenseItem(BaseModel):
    id_proveedor: str
    nombre_proveedor: str
    gasto_total: float
    numero_oc: int


class ReportProviderDeliveryItem(BaseModel):
    id_proveedor: str
    nombre_proveedor: str
    tiempo_promedio_dias: float
    cotizaciones: int


# --------------------------------------------------------------------------
# Audit Log
# --------------------------------------------------------------------------

class AuditLogRead(BaseModel):
    id: uuid.UUID
    fecha: datetime
    id_usuario: uuid.UUID | None
    nombre_usuario: str | None
    email_usuario: str | None
    rol_usuario: str | None
    accion: str
    detalle: str | None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int