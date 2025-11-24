import os
import json
import boto3
from botocore.exceptions import ClientError

# ---------- Config ----------
CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}
PRODUCTS_TABLE = os.environ.get("PRODUCTS_TABLE", "PRODUCTS_TABLE")

dynamodb = boto3.resource("dynamodb")
productos_table = dynamodb.Table(PRODUCTS_TABLE)

# ---------- Helpers ----------
def _resp(code, payload=None):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json", **CORS_HEADERS},
        "body": json.dumps(payload or {}, ensure_ascii=False, default=str)
    }

def _parse_body(event):
    body = event.get("body", {})
    if isinstance(body, str):
        body = json.loads(body) if body.strip() else {}
    elif not isinstance(body, dict):
        body = {}
    return body

# ---------- Handler ----------
def lambda_handler(event, context):
    # Preflight
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    if method == "OPTIONS":
        return _resp(204, {})

    body = _parse_body(event)
    
    # Buscar por local_id y producto_id
    local_id = body.get("local_id")
    producto_id = body.get("producto_id")
    
    if not local_id:
        return _resp(400, {"error": "Falta el campo local_id en el body"})
    
    if not producto_id:
        return _resp(400, {"error": "Falta el campo producto_id en el body"})
    
    # Buscar producto
    try:
        response = productos_table.get_item(
            Key={"local_id": local_id, "producto_id": producto_id}
        )
    except ClientError as e:
        return _resp(500, {"error": f"Error al buscar producto: {str(e)}"})
    
    if "Item" not in response:
        return _resp(404, {"error": "Producto no encontrado"})
    
    return _resp(200, {"producto": response["Item"]})
