# Instrucciones de Uso del Token

## Cómo Enviar el Token

Puedes enviar el token de **dos formas** en el header `Authorization`:

### Opción 1: Solo el token (Recomendado)
```
Authorization: c9f454d1-9fa4-43a6-9b4c-3197c54df482
```

### Opción 2: Con Bearer (Estándar HTTP)
```
Authorization: Bearer c9f454d1-9fa4-43a6-9b4c-3197c54df482
```

**Nota:** El header puede ser `Authorization` o `authorization` (mayúsculas o minúsculas).

## Validación del Token

La validación se hace directamente consultando la tabla `Millas-Tokens-Usuarios` en DynamoDB:

1. **Verifica que el token existe** en la tabla
2. **Verifica que no ha expirado** comparando la fecha actual con el campo `expires`
3. **Obtiene el rol** del usuario desde el campo `rol` o `role`
4. **Verifica permisos** según el endpoint:
   - **Crear/Actualizar/Eliminar Productos**: Requiere rol `Admin` o `Gerente`
   - **Crear Pedidos**: Cualquier usuario autenticado
   - **Ver/Modificar Usuario**: Según reglas de autorización

## Formato de la Tabla de Tokens

La tabla `Millas-Tokens-Usuarios` debe tener:

```json
{
  "token": "c9f454d1-9fa4-43a6-9b4c-3197c54df482",
  "user_id": "usuario@ejemplo.com",
  "rol": "Admin",  // o "Gerente" o "Cliente"
  "expires": "2024-12-31 23:59:59"  // Formato: YYYY-MM-DD HH:MM:SS
}
```

## Endpoints que Requieren Token

### Products
- `POST /productos/create` - Requiere rol Admin o Gerente
- `PUT /productos/update` - Requiere rol Admin o Gerente
- `DELETE /productos/delete` - Requiere rol Admin o Gerente
- `POST /productos/id` - Requiere token válido
- `POST /productos/list` - Requiere token válido

### Clientes
- `POST /pedido/create` - Requiere token válido
- `GET /pedido/status` - Requiere token válido
- `POST /pedido/confirmar` - Requiere token válido

### Users
- `POST /users/password/change` - Requiere token válido
- `GET /users/me` - Requiere token válido
- `PUT /users/me` - Requiere token válido
- `DELETE /users/me` - Requiere token válido
- `POST /users/employee` - Requiere rol Admin o Gerente
- `PUT /users/employee` - Requiere rol Admin o Gerente
- `DELETE /users/employee` - Requiere rol Admin o Gerente
- `POST /users/employees/list` - Requiere rol Admin o Gerente

## Endpoints Públicos (No Requieren Token)

- `POST /users/register` - Registro de usuario
- `POST /users/login` - Login de usuario

## Ejemplo de Uso en Postman

1. **Hacer Login** para obtener un token:
   ```
   POST /users/login
   Body: {
     "correo": "admin@200millas.com",
     "contrasena": "admin123"
   }
   ```

2. **Copiar el token** de la respuesta

3. **Usar el token** en los siguientes requests:
   - Ir a la pestaña "Headers"
   - Agregar header: `Authorization`
   - Valor: `tu-token-aqui` (sin "Bearer ")

## Errores Comunes

### "Token requerido"
- No se envió el header `Authorization`
- El header está vacío

### "Token no existe"
- El token no está en la tabla `Millas-Tokens-Usuarios`
- El token es incorrecto

### "Token expirado"
- La fecha actual es mayor que el campo `expires` del token

### "Permiso denegado: se requiere rol Admin o Gerente"
- El usuario no tiene el rol necesario para ese endpoint
- Verificar el campo `rol` en la tabla de tokens
