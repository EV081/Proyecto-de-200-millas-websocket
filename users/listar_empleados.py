import os
import json
import math
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from auth_helper import get_bearer_token, validate_token_via_lambda

TABLE_EMPLEADOS           = os.getenv("TABLE_EMPLEADOS")
TABLE_USUARIOS            = os.getenv("TABLE_USUARIOS", "TABLE_USUARIOS")
TOKENS_TABLE_USERS        = os.getenv("TOKENS_TABLE_USERS", "TOKENS_TABLE_USERS")

CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}

dynamodb   = boto3.resource("dynamodb")

t_empleados = dynamodb.Table(TABLE_EMPLEADOS)
t_usuarios  = dynamodb.Table(TABLE_USUARIOS)
t_tokens    = dynamodb.Table(TOKENS_TABLE_USERS)

ROLES_PUEDEN_LISTAR = {"Admin", "Gerente"}

def _resp(code, payload):
    return {"statusCode": code, "headers": CORS_HEADERS, "body": json.dumps(payload)}

def _safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

def _get_correo_from_token(token: str):
    """Obtiene el correo del usuario desde el token en la tabla"""
    try:
        r = t_tokens.get_item(Key={"token": token})
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

    # 3. Autorización: solo Admin o Gerente pueden listar empleados
    if rol_aut not in ROLES_PUEDEN_LISTAR:
        return _resp(403, {"message": "No tienes permiso para listar empleados"})

    # 4. Parse body y parámetros
    try:
        body = json.loads(event.get("body") or "{}")
    except Exception:
        body = {}

    # Parámetros de paginación
    page = _safe_int(body.get("page", 0), 0)
    size = _safe_int(body.get("size", body.get("limit", 10)), 10)
    if size <= 0 or size > 100:
        size = 10
    if page < 0:
        page = 0

    # Filtros opcionales
    filtro_local_id = body.get("local_id")
    filtro_role = body.get("role") or body.get("rol")  # "Repartidor"/"Cocinero"/"Despachador"

    # 5. Decidir entre Query (si hay local_id) o Scan (todos los empleados)
    if filtro_local_id:
        # Query por local_id (partition key)
        query_args = {
            "KeyConditionExpression": Key("local_id").eq(filtro_local_id)
        }
        
        # Agregar filtro de role si existe
        if filtro_role:
            query_args["FilterExpression"] = Attr("role").eq(filtro_role)
        
        # Contar total
        count_args = query_args.copy()
        count_args["Select"] = "COUNT"
        total = 0
        lek = None
        while True:
            if lek:
                count_args["ExclusiveStartKey"] = lek
            rcount = t_empleados.query(**count_args)
            total += rcount.get("Count", 0)
            lek = rcount.get("LastEvaluatedKey")
            if not lek:
                break
        
        # Calcular páginas
        total_pages = math.ceil(total / size) if size > 0 else 0
        
        # Obtener items de la página solicitada
        query_args["Limit"] = size
        lek = None
        
        # Saltar páginas previas
        for _ in range(page):
            if lek:
                query_args["ExclusiveStartKey"] = lek
            rskip = t_empleados.query(**query_args)
            lek = rskip.get("LastEvaluatedKey")
            if not lek:
                return _resp(200, {
                    "contents": [],
                    "page": page,
                    "size": size,
                    "totalElements": total,
                    "totalPages": total_pages
                })
        
        # Ejecutar query para la página actual
        if lek:
            query_args["ExclusiveStartKey"] = lek
        rpage = t_empleados.query(**query_args)
        items = rpage.get("Items", [])
        
    else:
        # Scan (todos los empleados de todos los locales)
        scan_args = {}
        
        # Agregar filtro de role si existe
        if filtro_role:
            scan_args["FilterExpression"] = Attr("role").eq(filtro_role)
        
        # Contar total
        count_args = scan_args.copy()
        count_args["Select"] = "COUNT"
        total = 0
        lek = None
        while True:
            if lek:
                count_args["ExclusiveStartKey"] = lek
            rcount = t_empleados.scan(**count_args)
            total += rcount.get("Count", 0)
            lek = rcount.get("LastEvaluatedKey")
            if not lek:
                break
        
        # Calcular páginas
        total_pages = math.ceil(total / size) if size > 0 else 0
        
        # Obtener items de la página solicitada
        scan_args["Limit"] = size
        lek = None
        
        # Saltar páginas previas
        for _ in range(page):
            if lek:
                scan_args["ExclusiveStartKey"] = lek
            rskip = t_empleados.scan(**scan_args)
            lek = rskip.get("LastEvaluatedKey")
            if not lek:
                return _resp(200, {
                    "contents": [],
                    "page": page,
                    "size": size,
                    "totalElements": total,
                    "totalPages": total_pages
                })
        
        # Ejecutar scan para la página actual
        if lek:
            scan_args["ExclusiveStartKey"] = lek
        rpage = t_empleados.scan(**scan_args)
        items = rpage.get("Items", [])

    return _resp(200, {
        "contents": items,
        "page": page,
        "size": size,
        "totalElements": total,
        "totalPages": total_pages,
        "solicitado_por": correo_aut,
        "rol_solicitante": rol_aut
    })
