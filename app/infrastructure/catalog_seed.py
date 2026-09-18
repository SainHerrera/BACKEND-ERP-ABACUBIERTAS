"""Catálogo inicial de productos/proveedores para el endpoint de carga.

Replica 1:1 los SEED_PROVIDERS / SEED_PRODUCTS del frontend
(frontend/src/services/localStorage/seedData.ts) para poder poblar la base
de datos con los mismos datos de demostración.
"""

SEED_PROVIDERS = [
    {
        "nombre_empresa": "Aceros del Caribe S.A.S.",
        "nit": "900123456-1",
        "contacto": "Carlos Mendoza",
        "telefono": "3151234567",
        "email": "ventas@acerosdelcaribe.com",
        "direccion": "Av. Industrial 45 # 12-30",
        "ciudad": "Barranquilla",
        "categoria_material": "estructuras",
        "condiciones_pago": "30 días",
        "observaciones": "Proveedor principal de perfiles de acero",
        "estado": "preferente",
    },
    {
        "nombre_empresa": "Plásticos & Cubiertas Polímeros",
        "nit": "800654321-2",
        "contacto": "Lucía Gómez",
        "telefono": "3109876543",
        "email": "contacto@plasticospolimeros.co",
        "direccion": "Zona Industrial Cazucá Manzana 4",
        "ciudad": "Bogotá",
        "categoria_material": "cubiertas",
        "condiciones_pago": "15 días",
        "observaciones": "Distribuidor directo de tejas termoacústicas UPVC",
        "estado": "activo",
    },
    {
        "nombre_empresa": "Fijaciones & Tornillos Industriales",
        "nit": "860777888-3",
        "contacto": "Andrés Torres",
        "telefono": "3185551234",
        "email": "ventas@fijacionestornillos.com",
        "direccion": "Calle 13 # 68-45",
        "ciudad": "Bogotá",
        "categoria_material": "tornilleria",
        "condiciones_pago": "Contado",
        "observaciones": "Tornillería autoperforante y arandelas de neopreno",
        "estado": "activo",
    },
]

SEED_PRODUCTS = [
    {
        "nombre": "Cubierta UPVC Termoacústica 3 Capas 2.44m",
        "descripcion": "Teja termoacústica UPVC color blanco/terracota de 2.44m de longitud",
        "unidad_medida": "unidad",
        "precio_unitario": 85000.0,
        "stock_actual": 45,
        "stock_minimo": 20,
        "nombre_proveedor": "Plásticos & Cubiertas Polímeros",
    },
    {
        "nombre": "Perfil C 100x50x2mm 6m Galvanizado",
        "descripcion": "Correa en acero galvanizado para soporte estructural de cubiertas",
        "unidad_medida": "unidad",
        "precio_unitario": 62000.0,
        "stock_actual": 8,
        "stock_minimo": 15,
        "nombre_proveedor": "Aceros del Caribe S.A.S.",
    },
    {
        "nombre": 'Tornillo Autoperforante 2" Punta Broca con Arandela (Caja x 100)',
        "descripcion": "Tornillo galvanizado con arandela EPDM para fijación de cubiertas",
        "unidad_medida": "caja",
        "precio_unitario": 28000.0,
        "stock_actual": 5,
        "stock_minimo": 10,
        "nombre_proveedor": "Fijaciones & Tornillos Industriales",
    },
    {
        "nombre": "Lámina Policarbonato Alveolar 6mm 2.10x5.80m Cristal",
        "descripcion": "Lámina traslúcida alveolar con protección UV",
        "unidad_medida": "unidad",
        "precio_unitario": 175000.0,
        "stock_actual": 30,
        "stock_minimo": 10,
        "nombre_proveedor": "Plásticos & Cubiertas Polímeros",
    },
    {
        "nombre": "Caballete Articulado UPVC Blanco 1.05m",
        "descripcion": "Cumbrera articulada para remate superior de tejados UPVC",
        "unidad_medida": "unidad",
        "precio_unitario": 34000.0,
        "stock_actual": 2,
        "stock_minimo": 12,
        "nombre_proveedor": "Plásticos & Cubiertas Polímeros",
    },
]