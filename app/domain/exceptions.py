class EmailAlreadyRegistered(Exception):
    """El email ya existe en el sistema."""


class InvalidCredentials(Exception):
    """Email o contraseña incorrectos."""


class UserInactive(Exception):
    """El usuario está desactivado."""


class RegistrationDisabled(Exception):
    """El registro público está deshabilitado."""


class InvalidToken(Exception):
    """Token inválido, expirado o de tipo incorrecto."""


class UserNotFound(Exception):
    """El usuario solicitado no existe."""


class ProviderNotFound(Exception):
    """El proveedor solicitado no existe."""


class ProductNotFound(Exception):
    """El producto solicitado no existe."""


class ClientNotFound(Exception):
    """El cliente solicitado no existe."""


class MovementNotFound(Exception):
    """El movimiento solicitado no existe."""


class DuplicateProviderNit(Exception):
    """Ya existe un proveedor con ese NIT."""


class DuplicateClientNitCc(Exception):
    """Ya existe un cliente con ese NIT/CC."""


class DuplicateProductName(Exception):
    """Ya existe un producto con ese nombre."""


class InsufficientStock(Exception):
    """No hay stock suficiente para la operación."""


class InvalidQuantity(Exception):
    """La cantidad de la operación es inválida."""


class InvalidMovementType(Exception):
    """El tipo de movimiento es inválido."""


class QuotationNotFound(Exception):
    """La cotización solicitada no existe."""


class InvalidQuotationStatus(Exception):
    """El estado de la cotización es inválido."""


class InvalidQuotationTransition(Exception):
    """La transición de estado de la cotización no está permitida."""


class SaleNotFound(Exception):
    """El pedido de venta solicitado no existe."""


class InvalidSaleStatus(Exception):
    """El estado del pedido de venta es inválido."""


class InvalidSaleTransition(Exception):
    """La transición de estado del pedido de venta no está permitida."""


class PurchaseOrderNotFound(Exception):
    """La orden de compra solicitada no existe."""


class InvalidPurchaseOrderStatus(Exception):
    """El estado de la orden de compra es inválido."""


class InvalidPurchaseOrderTransition(Exception):
    """La transición de estado de la orden de compra no está permitida."""


class ProductNotInOrder(Exception):
    """El producto no pertenece a la orden indicada."""


class ReceiptExceedsOrdered(Exception):
    """No se puede recibir más de lo ordenado."""


class StockRequestNotFound(Exception):
    """La solicitud de stock solicitada no existe."""


class InvalidStockRequestStatus(Exception):
    """El estado de la solicitud de stock es inválido."""


class InvalidStockRequestTransition(Exception):
    """La transición de estado de la solicitud de stock no está permitida."""


class ProviderQuotationNotFound(Exception):
    """La cotización de proveedor solicitada no existe."""


class InsufficientProviderQuotations(Exception):
    """La solicitud no tiene suficientes cotizaciones de proveedor para seleccionar."""


class ProductDoesNotMatchRequest(Exception):
    """El producto de la cotización no corresponde al de la solicitud."""