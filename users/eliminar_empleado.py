import json
import os
import boto3
from botocore.exceptions import ClientError
from auth_helper import get_bearer_token, validate_token_via_lambda

# === ENV ===
TABLE_EMPLEADOS_NAME      = os.getenv("TABLE_EMPLEADOS", "TABLE_EMPLEADOS")
TABLE_USUARIOS_NAME       = os.getenv("USERS_TABLE", "USERS_TABLE")
TOKENS_TABLE_USERS        = os.getenv("TOKENS_TABLE_USERS", "TOKENS_TABLE_USERS")

CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}

# === AWS ===
dynamodb   = boto3.resource("dynamodb")

empleados_table = dynamodb.Table(TABLE_EMPLEADOS_NAME)
usuarios_table  = dynamodb.Table(TABLE_USUARIOS_NAME)
tokens_table    = dynamodb.Table(TOKENS_TABLE_USERS)

ROLES_PUEDEN_ELIMINAR = {"Admin", "Gerente"}

# ---------- Helpers ----------
def _resp(code, payload):
    return {"statusCode": code, "headers": CORS_HEADERS, "body": json.dumps(payload)}

def _parse_body(event):
    body = event.get("body", {})
    if isinstance(body, str):
        body = json.loads(body) if body.strip() else {}
    elif not isinstance(body, dict):
        body = {}
    return body

def _get_correo_from_token(token: str):
    """Obtiene el correo del usuario desde el token en la tabla"""
    try:
        r = tokens_table.get_item(Key={"token": token})
        item = r.get("Item")
        if not item:
            return None
        return item.get("user_id")
    except Exception:
        return None


# ---------- Handler ----------
def lambda_handler(event, context):
    # 1. Validar token mediante Lambda
    token = get_bearer_token(event)
    valido, err, rol_aut = validate_token_via_lambda(token)
    if not valido:
        return _resp(401, {"message": err or "Token inválido"})
    
    # 2. Obtener correo del usuario autenticado
    correo_aut = _get_correo_from_token(token)
    if not correo_aut:
        return _resp(401, {"message": "No se pudo obtener el usuario del token"})

    # 3) Autorización: solo Admin o Gerente pueden eliminar empleados
    if rol_aut not in ROLES_PUEDEN_ELIMINAR:
        return _resp(403, {"message": "No tienes permiso para eliminar empleados"})

    # 4) Parse body y validar las claves compuestas (local_id y dni)
    body = _parse_body(event)
    local_id = body.get("local_id")
    dni = body.get("dni")
    
    if not local_id:
        return _resp(400, {"message": "local_id es obligatorio"})
    if not dni:
        return _resp(400, {"message": "dni es obligatorio"})

    # 5) Verificar existencia usando la clave compuesta
    try:
        resp = empleados_table.get_item(Key={"local_id": local_id, "dni": dni})
    except ClientError as e:
        return _resp(500, {"message": f"Error al obtener empleado: {str(e)}"})

    if "Item" not in resp:
        return _resp(404, {"message": "Empleado no encontrado"})

    # 6) Eliminar (con condición por seguridad)
    try:
        empleados_table.delete_item(
            Key={"local_id": local_id, "dni": dni},
            ConditionExpression="attribute_exists(local_id) AND attribute_exists(dni)"
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return _resp(404, {"message": "Empleado no encontrado"})
    except ClientError as e:
        return _resp(500, {"message": f"Error al eliminar empleado: {str(e)}"})
    except Exception as e:
        return _resp(500, {"message": f"Error al eliminar empleado: {str(e)}"})

    return _resp(200, {
        "message": "Empleado eliminado correctamente",
        "eliminado_por": correo_aut,
        "rol_solicitante": rol_aut
    })
