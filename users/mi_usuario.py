import os
import json
import boto3
from botocore.exceptions import ClientError
from common_auth import get_bearer_token, get_user_from_token

# === ENV ===
TABLE_USUARIOS_NAME       = os.getenv("USERS_TABLE", "USERS_TABLE")

CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}

# === AWS ===
dynamodb = boto3.resource("dynamodb")

usuarios_table = dynamodb.Table(TABLE_USUARIOS_NAME)

# ---------- helpers ----------
def _resp(code, payload):
    return {"statusCode": code, "headers": CORS_HEADERS, "body": json.dumps(payload)}

# ---------- handler ----------
def lambda_handler(event, context):
    # Validar token y obtener usuario
    token = get_bearer_token(event)
    correo_aut, rol_aut, err = get_user_from_token(token)
    if err:
        return _resp(401, {"message": err})

    # 3) Target (query param ?correo=...), por defecto yo mismo
    qp = event.get("queryStringParameters") or {}
    correo_target = qp.get("correo", correo_aut)

    # 4) Obtener usuario target
    try:
        r = usuarios_table.get_item(Key={"correo": correo_target})
    except Exception as e:
        return _resp(500, {"message": f"Error al obtener usuario: {str(e)}"})

    if "Item" not in r:
        return _resp(404, {"message": "Usuario no encontrado"})

    user_target = r["Item"]
    rol_target  = user_target.get("rol") or user_target.get("role") or "Cliente"

    # 5) Autorización:
    #    - self: siempre ok
    #    - Admin: puede ver a cualquiera
    #    - Gerente: solo puede ver a Clientes
    permitido = (correo_aut == correo_target)
    if not permitido:
        if rol_aut == "Admin":
            permitido = True
        elif rol_aut == "Gerente" and rol_target == "Cliente":
            permitido = True

    if not permitido:
        return _resp(403, {"message": "No tienes permiso para ver este usuario"})

    # 6) Sanitizar salida
    user_sanit = dict(user_target)
    user_sanit.pop("contrasena", None)
    user_sanit.pop("password", None)
    user_sanit.pop("password_hash", None)

    return _resp(200, {"message": "Usuario encontrado", "usuario": user_sanit})
