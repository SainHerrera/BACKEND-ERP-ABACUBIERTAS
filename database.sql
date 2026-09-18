-- Esquema de referencia. La app crea las tablas en cada arranque (create_all)
-- y Alembic se puede adoptar más adelante si se requiere versionado.

-- Para re-inicializar la tabla en desarrollo, descomenta la línea siguiente:
-- drop table if exists users cascade;

create table if not exists users (
	id UUID DEFAULT gen_random_uuid() primary key,
	name varchar(26) not null,
	email varchar(50) not null unique,
	password varchar(256) not null,
	rol varchar(256) not null,
	status boolean default true,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Revocación de refresh tokens (logout / denylist por jti)
create table if not exists revoked_tokens (
	jti varchar(64) primary key,
	user_id UUID references users(id) on delete set null,
	expires_at TIMESTAMPTZ not null,
	revoked_at TIMESTAMPTZ DEFAULT NOW()
);

create table if not exists providers (
	id_proveedor UUID DEFAULT gen_random_uuid() primary key,
	nombre_empresa varchar(120) not null,
	nit varchar(30) not null unique,
	contacto varchar(100),
	telefono varchar(30),
	email varchar(120),
	direccion varchar(255),
	ciudad varchar(80),
	categoria_material varchar(50) not null default 'general',
	condiciones_pago varchar(120),
	observaciones text,
	estado varchar(20) not null default 'activo',
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

create table if not exists products (
	id_producto UUID DEFAULT gen_random_uuid() primary key,
	nombre varchar(150) not null,
	descripcion text,
	unidad_medida varchar(30) not null default 'unidad',
	precio_unitario numeric(12,2) not null default 0,
	stock_actual integer not null default 0,
	stock_minimo integer not null default 15,
	id_proveedor UUID references providers(id_proveedor) on delete set null,
	activo boolean default true,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

create table if not exists clients (
	id_cliente UUID DEFAULT gen_random_uuid() primary key,
	tipo_cliente varchar(20) not null default 'empresa',
	nombre_razon_social varchar(150) not null,
	nit_cc varchar(30) not null unique,
	nombre_contacto varchar(100),
	telefono varchar(30),
	email varchar(120),
	direccion varchar(255),
	ciudad varchar(80),
	observaciones text,
	estado varchar(20) not null default 'activo',
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

create table if not exists movements (
	id_movimiento UUID DEFAULT gen_random_uuid() primary key,
	id_producto UUID not null references products(id_producto),
	tipo varchar(10) not null,
	cantidad integer not null,
	referencia varchar(120),
	id_usuario UUID references users(id) on delete set null,
	fecha TIMESTAMPTZ not null DEFAULT NOW(),
	nota text
);

create index if not exists idx_movements_producto_fecha on movements(id_producto, fecha);

create table if not exists quotations (
	id_cotizacion UUID DEFAULT gen_random_uuid() primary key,
	numero_consecutivo varchar(20) not null unique,
	id_cliente UUID not null references clients(id_cliente) on delete restrict,
	id_usuario UUID references users(id) on delete set null,
	fecha_emision TIMESTAMPTZ not null DEFAULT NOW(),
	fecha_vencimiento TIMESTAMPTZ,
	estado varchar(12) not null default 'borrador',
	subtotal numeric(12,2) not null default 0,
	impuestos numeric(12,2) not null default 0,
	descuento numeric(12,2) not null default 0,
	total numeric(12,2) not null default 0,
	observaciones text,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

create table if not exists quotation_details (
	id_detalle_cotizacion UUID DEFAULT gen_random_uuid() primary key,
	id_cotizacion UUID not null references quotations(id_cotizacion) on delete cascade,
	id_producto UUID not null references products(id_producto) on delete restrict,
	descripcion varchar(200),
	cantidad integer not null,
	precio_unitario numeric(12,2) not null,
	descuento numeric(12,2) not null default 0,
	subtotal numeric(12,2) not null
);

create index if not exists idx_quotations_cliente_estado on quotations(id_cliente, estado);
create index if not exists idx_quotation_details_cotizacion on quotation_details(id_cotizacion);

create table if not exists sales (
	id_orden_venta UUID DEFAULT gen_random_uuid() primary key,
	numero_orden varchar(20) not null unique,
	id_cliente UUID not null references clients(id_cliente) on delete restrict,
	id_cotizacion UUID references quotations(id_cotizacion) on delete set null,
	id_usuario UUID references users(id) on delete set null,
	fecha_venta TIMESTAMPTZ not null DEFAULT NOW(),
	estado varchar(12) not null default 'pendiente',
	subtotal numeric(12,2) not null default 0,
	impuestos numeric(12,2) not null default 0,
	total numeric(12,2) not null default 0,
	observaciones text,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

create table if not exists sale_details (
	id_detalle_venta UUID DEFAULT gen_random_uuid() primary key,
	id_orden_venta UUID not null references sales(id_orden_venta) on delete cascade,
	id_producto UUID not null references products(id_producto) on delete restrict,
	descripcion varchar(200),
	cantidad integer not null,
	precio_unitario numeric(12,2) not null default 0,
	descuento numeric(12,2) not null default 0,
	subtotal numeric(12,2) not null default 0
);

create index if not exists idx_sales_cliente_estado on sales(id_cliente, estado);
create index if not exists idx_sale_details_venta on sale_details(id_orden_venta);

create table if not exists purchase_orders (
	id_orden_compra UUID DEFAULT gen_random_uuid() primary key,
	numero_oc varchar(20) not null unique,
	id_proveedor UUID not null references providers(id_proveedor) on delete restrict,
	nombre_proveedor varchar(150),
	fecha_emision TIMESTAMPTZ not null DEFAULT NOW(),
	estado varchar(20) not null default 'pendiente_aprobacion',
	observaciones text,
	id_solicitud UUID,
	numero_solicitud varchar(20),
	id_cotizacion UUID,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

create table if not exists purchase_order_details (
	id_detalle_oc UUID DEFAULT gen_random_uuid() primary key,
	id_orden_compra UUID not null references purchase_orders(id_orden_compra) on delete cascade,
	id_producto UUID not null references products(id_producto) on delete restrict,
	descripcion varchar(200),
	cantidad_ordenada integer not null,
	cantidad_recibida integer not null default 0,
	precio_unitario numeric(12,2) not null default 0,
	tiempo_entrega_dias integer
);

create index if not exists idx_purchase_orders_proveedor_estado on purchase_orders(id_proveedor, estado);
create index if not exists idx_po_details_orden on purchase_order_details(id_orden_compra);

-- Configuración global single-row (id = 1)
create table if not exists system_settings (
	id integer primary key,
	stock_minimo_default integer not null default 15,
	margen_utilidad_default integer not null default 30,
	catalogo_inicial_cargado boolean not null default true,
	aprobacion_oc_habilitada boolean not null default false,
	aprobacion_oc_monto_minimo numeric(12,2) not null default 5000000,
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

insert into system_settings (id) values (1)
on conflict (id) do nothing;

-- Usuarios de prueba (el password se reemplaza por el hash Argon2id al usarse la API)
insert into users (name, email, rol, password) values
('Jhon', 'jhonhdzb123@gmail.com', 'admin', 'prueba')
on conflict (email) do nothing;

select * from users;