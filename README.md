# Proyecto 200 Millas - Documentación API

Proyecto de microservicios serverless para gestión de usuarios, empleados y productos.

---

## Estructura de Bases de Datos

### Usuarios
- **PK**: `correo` (string)
- **Campos**: nombre, correo, contrasena, role
- **Roles**: Cliente, Gerente, Admin

### Productos
- **PK**: `local_id` (string)
- **SK**: `nombre` (string)
- **Campos**: precio, descripcion, categoria, stock, imagen_url
- **Categorías**: Promos Fast, Express, Promociones, Sopas Power, Bowls Del Tigre, Leche de Tigre, Ceviches, Fritazo, Mostrimar, Box Marino, Duos Marinos, Trios Marinos, Dobles, Rondas Marinas, Mega Marino, Familiares

### Empleados
- **PK**: `local_id` (string)
- **SK**: `dni` (string)
- **Campos**: nombre, apellido, role, ocupado
- **Roles**: Repartidor, Cocinero, Despachador

---

## Microservicios

### 1. Service Users (`service-users`)

Gestiona autenticación, usuarios y empleados.

**Variables de Entorno**:
- `TABLE_USUARIOS`
- `TABLE_TOKENS_USUARIOS`
- `TABLE_EMPLEADOS`
- `TOKEN_VALIDATOR_FUNCTION`

#### Usuarios (Públicos)

| API | Método | Path | Request | Response |
|-----|--------|------|---------|----------|
| **Registrar Usuario** | POST | `/users/register` | `{nombre, correo, contrasena, role}` | `{message, correo}` |
| **Login** | POST | `/users/login` | `{correo, contrasena}` | `{token, expires_iso}` |

#### Usuarios (Protegidos - Require Token)

| API | Método | Path | Request | Response |
|-----|--------|------|---------|----------|
| **Obtener Mi Usuario** | GET | `/users/me` | - | `{nombre, correo, role}` |
| **Modificar Usuario** | PUT | `/users/me` | `{nombre?, contrasena?}` | `{message}` |
| **Eliminar Usuario** | DELETE | `/users/me` | - | `{message}` |
| **Cambiar Contraseña** | POST | `/users/password/change` | `{contrasena_actual, contrasena_nueva}` | `{message}` |

#### Empleados (Protegidos - Admin/Gerente)

| API | Método | Path | Request | Response |
|-----|--------|------|---------|----------|
| **Crear Empleado** | POST | `/users/employee` | `{local_id, dni, nombre, apellido, role, ocupado}` | `{message, employee}` |
| **Actualizar Empleado** | PUT | `/users/employee` | `{local_id, dni, ...campos_a_actualizar}` | `{message}` |
| **Eliminar Empleado** | DELETE | `/users/employee` | `{local_id, dni}` | `{message}` |
| **Listar Empleados** | POST | `/users/employees/list` | `{local_id, limit?, start_key?}` | `{empleados, count}` |

---

### 2. Service Products (`service-products`)

Gestiona operaciones CRUD de productos.

**Variables de Entorno**:
- `PRODUCTS_TABLE`
- `PRODUCTS_BUCKET` (S3 para imágenes)
- `TOKEN_VALIDATOR_FUNCTION`

| API | Método | Path | Request | Response |
|-----|--------|------|---------|----------|
| **Crear Producto** | POST | `/productos/create` | `{local_id, nombre, precio, descripcion, categoria, stock, imagen_url}` | `{message, producto}` |
| **Actualizar Producto** | PUT | `/productos/update` | `{local_id, nombre, ...campos_a_actualizar}` | `{message}` |
| **Obtener por ID** | POST | `/productos/id` | `{local_id, nombre}` | `{producto}` |
| **Listar Productos** | POST | `/productos/list` | `{local_id, limit?, start_key?}` | `{productos, count}` |
| **Eliminar Producto** | DELETE | `/productos/delete` | `{local_id, nombre}` | `{message}` |

---

### 3. Servicio clientes

| API                           | Método | Path                | Request                                                                                                   | Response                         |
| ----------------------------- | ------ | ------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------- |
| **Crear Pedido**              | POST   | `/pedido/create`    | `{tenant_id, local_id, usuario_correo, direccion, costo, estado, productos[], fecha_entrega_aproximada?}` | `{message, pedido}`              |
| **Obtener Estado del Pedido** | GET    | `/pedido/status`    | `?tenant_id=&pedido_id=`                                                                                  | `{tenant_id, pedido_id, estado}` |
| **Confirmar Recepción**       | POST   | `/pedido/confirmar` | `{tenant_id, pedido_id}`                                                                                  | `{message, estado: "recibido"}`  |

---

## Autenticación

- Endpoints **públicos**: No requieren token
- Endpoints **protegidos**: Requieren header `Authorization: Bearer <token>`
- El token se obtiene del endpoint de login
- El validador invoca a `TOKEN_VALIDATOR_FUNCTION` para verificar tokens

