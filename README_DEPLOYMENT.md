# Script de Despliegue Backend - Proyecto 200 Millas

Este script automatiza el despliegue completo del backend del proyecto.

## 🚀 Uso

```bash
./setup_backend.sh
```

## 📋 Opciones del Menú

1. **🏗️ Desplegar todo** - Crea infraestructura y despliega todos los microservicios
2. **🗑️ Eliminar todo** - Elimina microservicios e infraestructura
3. **📊 Solo infraestructura** - Crea tablas DynamoDB, S3 y pobla datos
4. **🚀 Solo microservicios** - Despliega solo los servicios Lambda
5. **❌ Salir**

## 🔧 Servicios Desplegados

Cuando seleccionas la opción 1 o 4, se despliegan:

### Servicios Principales
- **users/** - Gestión de usuarios y autenticación
- **clientes/** - Endpoints para clientes
- **products/** - Gestión de productos

### Step Functions
- **stepFunction/** - Orquestación del flujo de pedidos
  - Lambdas para cada estado del workflow
  - Colas SQS (Cola_Cocina, Cola_Delivery)
  - EventBridge rules

### Servicio de Empleados
- **servicio-empleados/** - API Gateway para empleados
  - 6 endpoints para gatillar eventos del workflow
  - Integración con EventBridge

## 📦 Infraestructura Creada

### DynamoDB Tables
- `t_usuarios` - Usuarios del sistema
- `t_empleados` - Empleados
- `t_locales` - Locales/restaurantes
- `t_productos` - Catálogo de productos
- `t_pedidos` - Pedidos
- `t_historial_estados` - Historial de estados de pedidos
- `t_tokens_usuarios` - Tokens de autenticación

### S3 Buckets
- Bucket de imágenes de productos

### SQS Queues
- `Cola_Cocina` - Cola para procesamiento en cocina
- `Cola_Delivery` - Cola para delivery

## ⚙️ Requisitos Previos

1. **AWS CLI** configurado con credenciales
2. **Serverless Framework** instalado (`npm i -g serverless`)
3. **Python 3** y **pip3**
4. **Archivo .env** configurado (copia de `.env.example`)

## 📝 Variables de Entorno Requeridas

Asegúrate de tener estas variables en tu `.env`:

```bash
AWS_ACCOUNT_ID=tu-account-id
AWS_REGION=us-east-1
ORG_NAME=tu-organizacion

TABLE_USUARIOS=t_usuarios
TABLE_EMPLEADOS=t_empleados
TABLE_LOCALES=t_locales
TABLE_PRODUCTOS=t_productos
TABLE_PEDIDOS=t_pedidos
TABLE_HISTORIAL_ESTADOS=t_historial_estados
TABLE_TOKENS_USUARIOS=t_tokens_usuarios

S3_BUCKET_NAME=tu-bucket-imagenes
```

## 🔄 Flujo de Despliegue

### Opción 1: Desplegar Todo

1. ✅ Valida variables de entorno
2. ✅ Crea bucket S3 de imágenes
3. ✅ Crea tablas DynamoDB
4. ✅ Genera datos de prueba
5. ✅ Pobla las tablas
6. ✅ Prepara Lambda Layer de dependencias
7. ✅ Despliega servicios principales
8. ✅ Despliega Step Functions
9. ✅ Despliega servicio de empleados

### Opción 2: Eliminar Todo

1. ⚠️ Solicita confirmación (escribe "SI")
2. 🗑️ Elimina servicio de empleados
3. 🗑️ Elimina Step Functions
4. 🗑️ Elimina servicios principales
5. 🗑️ Elimina tablas DynamoDB
6. 🗑️ Vacía y elimina bucket S3

## 🐛 Troubleshooting

### Error: "Falta [VARIABLE] en .env"
- Verifica que tu archivo `.env` tenga todas las variables requeridas

### Error: "sls: command not found"
- Instala Serverless Framework: `npm install -g serverless`

### Error: "AWS CLI no encontrado"
- Instala AWS CLI y ejecuta `aws configure`

### Error: "Table already exists"
- Si las tablas ya existen, usa la opción 4 (Solo microservicios)

### Error al desplegar Step Functions
- Recuerda que el Step Functions state machine debe crearse manualmente en AWS Console
- El script solo despliega las funciones Lambda, no el state machine

## 📚 Documentación Adicional

- [GUIA_PRUEBAS.md](stepFunction/GUIA_PRUEBAS.md) - Cómo probar el flujo completo
- [NOTA_TABLA_HISTORIAL.md](stepFunction/NOTA_TABLA_HISTORIAL.md) - Información sobre la tabla de historial
- [README.md](servicio-empleados/README.md) - Endpoints del servicio de empleados

## 🎯 Próximos Pasos Después del Despliegue

1. **Crear Step Functions State Machine** manualmente en AWS Console
   - Usa el JSON de `stepFunction/step_function_definition.json`
   
2. **Obtener URLs de API Gateway**
   - Revisa el output del despliegue para obtener las URLs
   
3. **Probar el flujo completo**
   - Sigue la guía en `stepFunction/GUIA_PRUEBAS.md`
