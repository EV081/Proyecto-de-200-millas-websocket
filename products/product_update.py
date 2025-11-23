import os, json, boto3
from decimal import Decimal, InvalidOperation
from datetime import datetime
from botocore.exceptions import ClientError

PRODUCTS_TABLE = os.environ.get("PRODUCTS_TABLE", "")
TOKENS_TABLE = os.environ.get("TOKENS_TABLE_USERS", "TOKENS_TABLE_USERS")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,POST"
}

ALLOWED_ROLES = {"Admin", "Gerente"}

dynamodb = boto3.resource("dynamodb")
tokens_table = dynamodb.Table(TOKENS_TABLE)

def _resp(code, body):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json", **CORS_HEADERS},
        "body": json.dumps(body, ensure_ascii=False, default=str)
    }

def _parse_body(event):
    body = event.get("body") or "{}"
    if isinstance(body, str):
        body = body if body.strip() else "{}"
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}
    return body if isinstance(body, dict) else {}

def _to_decimal(obj):
    """int/float -> Decimal (recursivo)."""
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(x) for x in obj]
    if isinstance(obj, (bool, type(None), Decimal, str)):
        return obj
    if isinstance(obj, (int, float)):
        return Decimal(str(obj))
    return obj

def _get_token(event):
    """Extrae el token del header Authorization"""
    headers = event.get("headers") or {}
    for key, value in headers.items():
        if key.lower() == "authorization":
            token = value.strip()
            if token.lower().startswith("bearer "):
                return token.split(" ", 1)[1].strip()
            return token
    return None

def _validate_token_and_role(token):
    """Valida el token y verifica que sea Admin o Gerente"""
    if not token:
        return False, "Token requerido", None
    
    try:
        response = tokens_table.get_item(Key={'token': token})
        
        if 'Item' not in response:
            return False, "Token no existe", None
        
        item = response['Item']
        expires_str = item.get('expires')
        
        if not expires_str:
            return False, "Token sin fecha de expiración", None
        
        # Parsear fecha de expiración (soporta múltiples formatos)
        try:
            # Intentar formato ISO 8601: 2025-11-23T02:28:53.290513
            if 'T' in expires_str:
                # Remover microsegundos si existen
                if '.' in expires_str:
                    expires_str = expires_str.split('.')[0]
                expires_dt = datetime.strptime(expires_str, '%Y-%m-%dT%H:%M:%S')
            else:
                # Formato simple: 2025-11-23 02:28:53
                expires_dt = datetime.strptime(expires_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return False, "Formato de fecha inválido", None
        
        # Comparar con fecha actual
        now = datetime.now()
        if now > expires_dt:
            return False, "Token expirado", None
        
        rol = item.get('rol') or item.get('role') or "Cliente"
        
        if rol not in ALLOWED_ROLES:
            return False, "Permiso denegado: se requiere rol Admin o Gerente", None
        
        return True, None, rol
        
    except Exception as e:
        return False, f"Error al validar token: {str(e)}", None



def lambda_handler(event, context):
    # CORS preflight
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    if method == "OPTIONS":
        return _resp(204, {})

    if not PRODUCTS_TABLE:
        return _resp(500, {"error": "PRODUCTS_TABLE no configurado"})

    # Validar token y rol
    token = _get_token(event)
    valido, error, rol = _validate_token_and_role(token)
    if not valido:
        return _resp(403, {"error": error or "Token inválido"})

    # --- Body ---
    raw = _parse_body(event)
    data = _to_decimal(raw)

    # Claves admitidas:
    #   esquema legado: tenant_id + product_id
    #   esquema actual: local_id + nombre
    tenant_id = data.pop("tenant_id", None)
    product_id = data.pop("product_id", None)
    local_id   = data.pop("local_id", None)
    nombre     = data.pop("nombre", None)

    # Resolver clave real a usar
    key = None
    if tenant_id and product_id:
        key = {"tenant_id": tenant_id, "product_id": product_id}
        pk_name, sk_name = "tenant_id", "product_id"
    elif local_id and nombre:
        key = {"local_id": local_id, "nombre": nombre}
        pk_name, sk_name = "local_id", "nombre"
    else:
        # Mensaje claro según lo que falte
        return _resp(400, {"error": "Faltan claves. Usa (tenant_id, product_id) o (local_id, nombre)"})

    # No permitir que intenten cambiar PK/SK en el update:
    for forbidden in ("tenant_id", "product_id", "local_id", "nombre"):
        if forbidden in data:
            data.pop(forbidden, None)

    if not data:
        return _resp(400, {"error": "Body vacío; nada que actualizar"})

    # Construir UpdateExpression seguro
    expr_names, expr_values, sets = {}, {}, []
    idx = 0
    for k, v in data.items():
        idx += 1
        name_key = f"#f{idx}"
        value_key = f":v{idx}"
        expr_names[name_key] = k
        expr_values[value_key] = v
        sets.append(f"{name_key} = {value_key}")
    update_expr = "SET " + ", ".join(sets)

    ddb = boto3.resource("dynamodb")
    table = ddb.Table(PRODUCTS_TABLE)

    try:
        res = table.update_item(
            Key=key,
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ConditionExpression=f"attribute_exists({pk_name}) AND attribute_exists({sk_name})",
            ReturnValues="ALL_NEW"
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code == "ConditionalCheckFailedException":
            return _resp(404, {"error": "Producto no encontrado"})
        return _resp(500, {"error": f"Error al actualizar: {e}"})
    except Exception as e:
        return _resp(500, {"error": f"Error inesperado: {e}"})

    return _resp(200, {"ok": True, "item": res.get("Attributes")})
