# 📊 Analytics - 200 Millas

Sistema de analytics usando AWS Glue, Athena y S3 para análisis de datos de pedidos.

## Arquitectura

```
DynamoDB Tables
    ↓
Lambda (Export)
    ↓
S3 Bucket (bucket-analytic)
    ↓
Glue Crawlers
    ↓
Glue Database
    ↓
Athena Queries
    ↓
API Endpoints
```

## Componentes

### 1. Exportación de Datos
- **Función**: `ExportDynamoDBToS3`
- **Descripción**: Exporta datos de DynamoDB a S3 en formato JSON
- **Tablas**: `Millas-Pedidos`, `Millas-Historial-Estados`
- **Destino**: `s3://bucket-analytic-{account-id}/`

### 2. Glue Crawlers
- **millas-pedidos-crawler**: Escanea `s3://bucket-analytic-{account-id}/pedidos/`
- **millas-historial-crawler**: Escanea `s3://bucket-analytic-{account-id}/historial_estados/`
- **Database**: `millas_analytics_db`

### 3. Queries de Athena

#### Query 1: Total de Pedidos por Local
- **Endpoint**: `GET /analytics/pedidos-por-local`
- **Descripción**: Cuenta el total de pedidos agrupados por local
- **Tabla**: `pedidos`

**Ejemplo de respuesta:**
```json
{
  "query": "Total de pedidos por local",
  "data": [
    {
      "local_id": "LOCAL-001",
      "total_pedidos": 150
    },
    {
      "local_id": "LOCAL-002",
      "total_pedidos": 120
    }
  ]
}
```

#### Query 2: Ganancias Totales por Local
- **Endpoint**: `GET /analytics/ganancias-por-local`
- **Descripción**: Calcula ganancias totales y promedio por local
- **Tabla**: `pedidos`

**Ejemplo de respuesta:**
```json
{
  "query": "Ganancias totales por local",
  "data": [
    {
      "local_id": "LOCAL-001",
      "total_pedidos": 150,
      "ganancias_totales": 4500.50,
      "ganancia_promedio": 30.00
    }
  ]
}
```

#### Query 3: Tiempo Total de Pedido
- **Endpoint**: `GET /analytics/tiempo-pedido`
- **Descripción**: Calcula el tiempo desde "procesando" hasta "recibido"
- **Tabla**: `historial_estados`

**Ejemplo de respuesta:**
```json
{
  "query": "Tiempo total de pedido (procesado -> recibido)",
  "data": [
    {
      "pedido_id": "abc-123",
      "inicio": "2024-11-23T10:00:00",
      "fin": "2024-11-23T11:30:00",
      "tiempo_total_minutos": 90,
      "tiempo_total_horas": 1
    }
  ]
}
```

#### Query 4: Promedio de Tiempo por Estado
- **Endpoint**: `GET /analytics/promedio-por-estado`
- **Descripción**: Calcula el tiempo promedio que los pedidos pasan en cada estado
- **Tabla**: `historial_estados`

**Ejemplo de respuesta:**
```json
{
  "query": "Promedio de tiempo por estado",
  "data": [
    {
      "estado": "procesando",
      "total_pedidos": 100,
      "tiempo_promedio_minutos": 15.5,
      "tiempo_minimo_minutos": 5,
      "tiempo_maximo_minutos": 30,
      "desviacion_estandar": 5.2
    }
  ]
}
```

## Despliegue

### Automático (con setup_backend.sh)
```bash
./setup_backend.sh
# Seleccionar opción 1 (Desplegar todo)
```

### Manual
```bash
cd analytics
bash setup_analytics.sh
```

## Uso

### 1. Exportar Datos Manualmente
```bash
aws lambda invoke \
  --function-name service-analytics-dev-ExportDynamoDBToS3 \
  --region us-east-1 \
  /tmp/response.json
```

### 2. Ejecutar Crawlers Manualmente
```bash
# Crawler de pedidos
aws glue start-crawler --name millas-pedidos-crawler --region us-east-1

# Crawler de historial
aws glue start-crawler --name millas-historial-crawler --region us-east-1
```

### 3. Verificar Tablas en Glue
```bash
aws glue get-tables \
  --database-name millas_analytics_db \
  --region us-east-1
```

### 4. Consultar Endpoints
```bash
# Total de pedidos por local
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/analytics/pedidos-por-local

# Ganancias por local
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/analytics/ganancias-por-local

# Tiempo de pedido
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/analytics/tiempo-pedido

# Promedio por estado
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/analytics/promedio-por-estado
```

## Estructura de Archivos

```
analytics/
├── serverless.yml                      # Configuración de Serverless
├── export_to_s3.py                     # Exporta DynamoDB a S3
├── query_pedidos_por_local.py          # Query 1
├── query_ganancias_por_local.py        # Query 2
├── query_tiempo_pedido.py              # Query 3
├── query_promedio_por_estado.py        # Query 4
├── setup_analytics.sh                  # Script de setup
└── README.md                           # Este archivo
```

## Recursos Creados

### S3 Buckets
- `bucket-analytic-{account-id}` - Almacena datos exportados
- `athena-results-{account-id}` - Almacena resultados de Athena

### Glue
- Database: `millas_analytics_db`
- Crawlers: `millas-pedidos-crawler`, `millas-historial-crawler`
- Tables: `pedidos`, `historial_estados`

### Athena
- Workgroup: `millas-analytics-workgroup`

### Lambda Functions
- `service-analytics-dev-ExportDynamoDBToS3`
- `service-analytics-dev-TotalPedidosPorLocal`
- `service-analytics-dev-GananciasPorLocal`
- `service-analytics-dev-TiempoPedido`
- `service-analytics-dev-PromedioPedidosPorEstado`

## Troubleshooting

### Error: "Table not found"
- Ejecutar los crawlers manualmente
- Esperar 1-2 minutos para que terminen
- Verificar que las tablas existan en Glue

### Error: "No data"
- Verificar que hay datos en DynamoDB
- Ejecutar la exportación manualmente
- Verificar que los archivos JSON estén en S3

### Error: "Query timeout"
- Aumentar el timeout en las funciones Lambda
- Verificar que Athena tenga permisos correctos

## Notas

- La exportación se puede programar con EventBridge (actualmente deshabilitado)
- Los crawlers detectan automáticamente el esquema de los datos
- Athena cobra por datos escaneados (~$5 por TB)
- Los resultados se cachean en S3 para consultas repetidas
