# Cambios en la Validación de Tokens

## Resumen
Se ha implementado un sistema centralizado de validación de tokens que consulta directamente la tabla de tokens en DynamoDB, eliminando las invocaciones entre servicios Lambda que causaban errores 403 y 500.

## Archivo Común Creado

### `common_auth.py`
Archivo compartido que contiene las funciones de validación de tokens:

- `get_bearer_token(event)`: Extrae el token del header Authorization
- `validate_token(token)`: Valida el token consultando la tabla de tokens
  - Verifica que el token existe
  - Verifica que no ha expirado
  - Retorna: (valido: bool, error: str, token_data: dict)
- `get_user_from_token(token)`: Obtiene correo y rol del usuario desde el token
  - Retorna: (correo: str, rol: str, error: str)

Este archivo se copió a las carpetas: `products/`, `clientes/`, y `users/`

## Servicios Actualizados

### 1. Products (products/)
**Archivos modificados:**
- `product_create.py`: Ahora valida tokens directamente
- `product_update.py`: Valida tokens y verifica rol Admin/Gerente
- `product_delete.py`: Valida tokens y verifica rol Admin/Gerente
- `serverless.yml`: Eliminados los authorizers de API Gateway

### 2. Clientes (clientes/)
**Archivos modificados:**
- `pedido_create.py`: Valida tokens directamente
- `estado_pedido.py`: Valida tokens directamente
- `confirmar_recepcion.py`: Valida tokens directamente
- `serverless.yml`: Eliminados los authorizers de API Gateway

### 3. Users (users/)
**Archivos modificados:**
- `mi_usuario.py`: Valida tokens directamente
- `cambiar_contrasena.py`: Valida tokens directamente
- `modificar_usuario.py`: Valida tokens directamente (parcial)
- `eliminar_usuario.py`: Valida tokens directamente (parcial)
- `serverless.yml`: Eliminados los authorizers de API Gateway

## Cómo Funciona Ahora

1. **Extracción del Token**: Se obtiene del header `Authorization: Bearer <token>`
2. **Validación**: Se consulta la tabla `TOKENS_TABLE_USERS` (Millas-Tokens-Usuarios)
3. **Verificación de Expiración**: Se compara la fecha actual con el campo `expires`
4. **Obtención de Datos**: Se extrae `user_id` (correo) y `rol` del token
5. **Autorización**: Cada endpoint verifica los permisos según el rol

## Ejemplo de Uso en una Lambda

```python
from common_auth import get_bearer_token, get_user_from_token

def lambda_handler(event, context):
    # Validar token y obtener usuario
    token = get_bearer_token(event)
    correo, rol, error = get_user_from_token(token)
    
    if error:
        return {
            "statusCode": 403,
            "body": json.dumps({"error": error})
        }
    
    # Verificar permisos según rol
    if rol not in ("Admin", "Gerente"):
        return {
            "statusCode": 403,
            "body": json.dumps({"error": "Permiso denegado"})
        }
    
    # Continuar con la lógica del endpoint...
```

## Ventajas del Nuevo Enfoque

1. **Sin invocaciones entre Lambdas**: Elimina los errores de permisos y ARNs incorrectos
2. **Más rápido**: Una sola consulta a DynamoDB en lugar de invocar otra Lambda
3. **Más simple**: Código más fácil de entender y mantener
4. **Consistente**: Todos los servicios usan la misma lógica de validación
5. **Menos costoso**: Menos invocaciones de Lambda = menos costos

## Variables de Entorno Requeridas

Todos los servicios necesitan:
```yaml
environment:
  TOKENS_TABLE_USERS: ${env:TABLE_TOKENS_USUARIOS}
```

## Próximos Pasos

Los siguientes archivos aún necesitan ser actualizados completamente:
- `users/modificar_usuario.py`
- `users/eliminar_usuario.py`
- `users/register_empleado.py`
- `users/actualizar_empleado.py`
- `users/eliminar_empleado.py`
- `users/listar_empleados.py`

Estos archivos tienen actualizaciones parciales pero pueden necesitar limpieza adicional.
