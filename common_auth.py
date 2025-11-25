import os
import boto3
from datetime import datetime, timezone

TOKENS_TABLE_USERS = os.environ.get("TOKENS_TABLE_USERS", "TOKENS_TABLE_USERS")

def get_bearer_token(event):
    """Extrae el token del header Authorization (con o sin 'Bearer ')"""
    headers = event.get("headers") or {}
    
    # Buscar el header Authorization (case-insensitive)
    auth_header = None
    for key, value in headers.items():
        if key.lower() == "authorization":
            auth_header = value
            break
    
    if not auth_header:
        return None
    
    # Si es string, procesar
    if isinstance(auth_header, str):
        auth_header = auth_header.strip()
        
        # Si tiene "Bearer ", extraer el token
        if auth_header.lower().startswith("bearer "):
            return auth_header.split(" ", 1)[1].strip()
        
        # Si no tiene "Bearer ", devolver el token directamente
        return auth_header
    
    return None

def validate_token(token):
    """
    Valida el token consultando la tabla de tokens.
    Retorna (valido: bool, error: str, token_data: dict)
    """
    if not token:
        return False, "Token requerido", None
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(TOKENS_TABLE_USERS)
        response = table.get_item(Key={'token': token})
        
        if 'Item' not in response:
            return False, "Token no existe", None
        
        item = response['Item']
        expires_str = item.get('expires')
        
        if not expires_str:
            return False, "Token sin fecha de expiración", None
        
        # Parsear fecha de expiración
        try:
            expires_dt = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return False, "Formato de expiración inválido", None
        
        now_utc = datetime.now(timezone.utc)
        if now_utc > expires_dt:
            return False, "Token expirado", None
        
        return True, None, item
        
    except Exception as e:
        return False, f"Error al validar token: {str(e)}", None

def get_user_from_token(token):
    """
    Obtiene el correo y rol del usuario desde el token.
    Retorna (correo: str, rol: str, error: str)
    """
    valido, error, token_data = validate_token(token)
    
    if not valido:
        return None, None, error
    
    correo = token_data.get("user_id") or token_data.get("correo") or token_data.get("email")
    rol = token_data.get("rol") or token_data.get("role") or "Cliente"
    
    if not correo:
        return None, None, "Token sin usuario asociado"
    
    return correo, rol, None
