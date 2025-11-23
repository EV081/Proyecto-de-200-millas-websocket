import os
import json
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError
from common_auth import get_bearer_token, get_user_from_token

TABLE_PEDIDOS = os.environ["TABLE_PEDIDOS"]

dynamodb = boto3.resource("dynamodb")
pedidos_table = dynamodb.Table(TABLE_PEDIDOS)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,GET"
}

def _resp(code, body):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json", **CORS_HEADERS},
        "body": json.dumps(body, ensure_ascii=False, default=str)
    }



def lambda_handler(event, context):
    # CORS preflight
    method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method"))
    if method == "OPTIONS":
        return _resp(200, {"ok": True})

    # Solo GET
    if method != "GET":
        return _resp(405, {"error": "Método no permitido"})

    # Validar token y obtener usuario
    token = get_bearer_token(event)
    correo_token, rol, error = get_user_from_token(token)
    if error:
        return _resp(403, {"error": error})

    # Params: tenant_id y pedido_id por querystring
    qs = event.get("queryStringParameters") or {}
    tenant_id = (qs.get("tenant_id") or "").strip()
    pedido_id = (qs.get("pedido_id") or "").strip()
    if not tenant_id or not pedido_id:
        return _resp(400, {"error": "Faltan parámetros tenant_id y/o pedido_id"})

    # Leer pedido
    try:
        r = pedidos_table.get_item(Key={"tenant_id": tenant_id, "pedido_id": pedido_id})
    except ClientError as e:
        print(f"Error get_item pedidos: {e}")
        return _resp(500, {"error": "Error consultando el pedido"})

    item = r.get("Item")
    if not item:
        return _resp(404, {"error": "Pedido no encontrado"})

    # AutZ: el pedido debe pertenecer al usuario del token
    if item.get("usuario_correo") != correo_token:
        return _resp(403, {"error": "No autorizado a consultar este pedido"})

    # Respuesta mínima (estado del pedido)
    return _resp(200, {
        "tenant_id": tenant_id,
        "pedido_id": pedido_id,
        "estado": item.get("estado"),
    })
