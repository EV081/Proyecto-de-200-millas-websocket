# 200 Millas – Serverless Auth + Productos (README)

Guía rápida para cualquier dev que abra el repo y quiera ejecutarlo, entender el **flujo end-to-end** y continuar el desarrollo.

---

## Arquitectura (MVP)

* **API Gateway (HTTP API)**

  * `/usuarios/crear` → Lambda **CrearUsuario**
  * `/usuarios/login` → Lambda **LoginUsuario**
  * `/productos/upload-url` → Lambda **GetUploadUrl** (firma subida a S3)
  * `/productos/crear` → Lambda **CrearProducto**
* **Lambdas (Python 3.12)**
* **DynamoDB**

  * `t_usuarios` (PK `tenant_id`, SK `user_id`)
  * `t_tokens_acceso` (PK `token`)
  * `t_productos` (PK `tenant_id`, SK `product_id`)
* **S3**: `PRODUCTS_BUCKET` para imágenes de productos
* **Multitenancy**: se agrupa todo por `tenant_id` (ej. `6200millas`)

---

## Requisitos

* Node.js + Serverless Framework v4
* Python 3.12
* AWS Academy **LabRole** (ARN en `provider.iam.role`)
* Credenciales AWS configuradas (Cloud9 o CLI)

---

## Estructura del proyecto

```
.
├── serverless.yml
└── src/
    ├── __init__.py
    ├── common.py                # helpers (hash, response)
    ├── crear_usuario.py
    ├── login_usuario.py
    ├── validar_token.py
    ├── _auth.py                 # validar token (lee t_tokens_acceso)
    ├── productos_get_upload_url.py
    └── productos_crear.py
```

---

## Variables de entorno (definidas en `serverless.yml`, provider.environment)

* `USERS_TABLE=t_usuarios`
* `TOKENS_TABLE=t_tokens_acceso`
* `PRODUCTS_TABLE=t_productos`
* `PRODUCTS_BUCKET=productos-200millas-dev` (o el que se despliegue)

---

## Despliegue

```bash
npm i -g serverless
sls deploy
```

> El `serverless.yml` ya incluye el ARN del LabRole. Si cambia tu región o bucket, ajústalo ahí.

---

## Modelos de datos

### `t_usuarios`

```json
{
  "tenant_id": "6200millas",      // PK
  "user_id": "chef@6200millas.pe",// SK
  "password_hash": "sha256...",
  "created_at": "2025-11-08T12:34:56Z"
}
```

### `t_tokens_acceso`

```json
{
  "token": "uuid",                 // PK
  "tenant_id": "6200millas",
  "user_id": "chef@6200millas.pe",
  "expires": "YYYY-MM-DD HH:MM:SS"
}
```

### `t_productos`

```json
{
  "tenant_id": "6200millas",       // PK
  "product_id": "uuid",            // SK
  "name": "Ceviche Clásico",
  "price": 38.5,                   // Decimal (boto3 Decimal)
  "offer": 3.5,                    // Decimal
  "image_key": "tenants/6200millas/products/<uuid>.png",
  "created_at": "2025-11-08T12:34:56Z"
}
```

---

## Flujos principales

### 1) Registro y Login

1. `POST /usuarios/crear` → guarda usuario (hash sha256) en `t_usuarios`.
2. `POST /usuarios/login` → valida credenciales; genera `token` (uuid) y `expires`; guarda en `t_tokens_acceso`.

### 2) Subir imagen (presigned URL) y crear producto

1. `POST /productos/upload-url` con `{ token, contentType }`

   * Valida el token.
   * Genera `product_id` y `image_key`.
   * Devuelve `uploadUrl` firmado de **S3** (PUT), `image_key`, `product_id`.
2. **Cliente** hace `PUT {{uploadUrl}}` con el archivo binario (header `Content-Type` igual al solicitado).
3. `POST /productos/crear` con `{ token, product_id, name, price, offer, image_key }`

   * Valida token y guarda el producto en `t_productos`.

> Ventaja: la imagen **no pasa por Lambda**. Escala y reduce costos.

---

## Endpoints (DEV)

* `POST /usuarios/crear`
* `POST /usuarios/login`
* `POST /productos/upload-url`
* `POST /productos/crear`

(Ver URL base real que imprime `sls deploy`.)

---

## Ejemplos (cURL)

### Registrar usuario

```bash
curl -X POST "$BASE/usuarios/crear" \
 -H "Content-Type: application/json" \
 -d '{"tenant_id":"6200millas","user_id":"chef@6200millas.pe","password":"Secreta123"}'
```

### Login

```bash
curl -X POST "$BASE/usuarios/login" \
 -H "Content-Type: application/json" \
 -d '{"tenant_id":"6200millas","user_id":"chef@6200millas.pe","password":"Secreta123"}'
# => {"token":"<uuid>","expires":"..."}
```

### Upload URL

```bash
curl -X POST "$BASE/productos/upload-url" \
 -H "Content-Type: application/json" \
 -d '{"token":"<TOKEN>","contentType":"image/png"}'
# => { "uploadUrl": "...", "image_key": "...", "product_id": "..." }
```

### Subir archivo a S3 (PUT)

```bash
curl -X PUT -H "Content-Type: image/png" \
 --upload-file ./ceviche.png "<uploadUrl>"
```

### Crear producto

```bash
curl -X POST "$BASE/productos/crear" \
 -H "Content-Type: application/json" \
 -d '{
  "token":"<TOKEN>",
  "product_id":"<PRODUCT_ID>",
  "name":"Ceviche Clásico",
  "price":38.5,
  "offer":3.5,
  "image_key":"<IMAGE_KEY>"
}'
```

---

## Colecciones Postman

* Auth (Register/Login): [Descargar](sandbox:/mnt/data/200millas_auth_collection.json)
* Environment DEV: [Descargar](sandbox:/mnt/data/200millas_dev_environment.json)

> Puedes añadir dos requests más: **Upload URL** (POST) y **Upload to S3 (PUT)** usando `binary` + `{{uploadUrl}}`, y **Crear Producto** (POST) tomando `{{product_id}}` y `{{image_key}}` de variables de entorno.

---

## Troubleshooting

* **500 en `/productos/upload-url`**

  * Asegúrate de tener `src/__init__.py` y usar `from ._auth import validate_token`.
  * Revisa `PRODUCTS_BUCKET` existente y permisos de `LabRole` (`s3:PutObject`).
* **403 al subir a S3**

  * Expiró el presigned URL (pídelo de nuevo).
  * `Content-Type` del PUT **no coincide** con el usado al firmar.
* **Float types are not supported**

  * Usar `Decimal` al escribir `price` y `offer` (ya corregido en `productos_crear.py`).
* **CORS**

  * Bucket S3 con CORS para `PUT` y `GET`. Si usarás front web, añade origen específico.

---

## Roadmap (siguientes hitos)

1. **Productos**

   * `GET /productos` (listar por tenant, paginado)
   * `PUT /productos/{id}` (actualizar)
   * `DELETE /productos/{id}`
   * Evitar duplicados por nombre usando GSI (`NAME#`)

2. **Autorización**

   * Aceptar `Authorization: Bearer <token>` en vez de `token` en el body (middleware).
   * TTL automático en `t_tokens_acceso` (atributo `ttl` + DynamoDB TTL).

3. **Frontend**

   * UI simple con Amplify Hosting (o S3+CF) que:

     * Haga login
     * Genere presigned URL y suba imagen
     * Cree producto y lo liste con imagen

4. **Observabilidad**

   * Logs estructurados (JSON)
   * Alarms (Lambda errors > 0, 5xx en API Gateway)

5. **Pedidos (workflow)**

   * Modelado: `t_pedidos` (status por evento)
   * Orquestación con **Step Functions** + **EventBridge** (Estados: recibido → cocina → empaque → reparto → entregado)

---

Con esto cualquier dev puede levantar el proyecto, entender el **por qué** de cada pieza y seguir construyendo sin perderse. Si quieres, te genero un `README.md` listo para agregar al repo.
