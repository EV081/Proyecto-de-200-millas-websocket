# 🔧 Solución: Error de Athena Output Location

## Problema
```
No output location provided. You did not provide an output location for your query results.
```

## Solución Rápida

### Opción 1: Ejecutar script de configuración
```bash
cd analytics
bash configure_athena.sh
```

### Opción 2: Configurar manualmente desde AWS Console

1. **Ir a Athena** en AWS Console
2. **Settings** (Configuración)
3. **Manage** (Administrar)
4. **Query result location**: `s3://athena-results-{tu-account-id}/results/`
5. **Save** (Guardar)

### Opción 3: Usar el Workgroup correcto

En la consola de Athena:
1. Cambiar a **Workgroup**: `millas-analytics-workgroup`
2. Este workgroup ya tiene configurado el output location

## Verificación

Después de configurar, prueba esta query:

```sql
SELECT * FROM pedidos LIMIT 10;
```

Si funciona, verás los resultados y se guardarán en:
```
s3://athena-results-{account-id}/results/
```

## Campos Correctos de las Tablas

### Tabla: pedidos
```sql
SELECT 
    pedido_id,
    local_id,
    tenant_id_usuario,
    costo,
    direccion,
    estado,
    created_at,
    productos
FROM pedidos
LIMIT 5;
```

### Tabla: historial_estados
```sql
SELECT 
    estado_id,
    pedido_id,
    estado,
    hora_inicio,
    hora_fin,
    empleado
FROM historial_estados
LIMIT 5;
```

## Queries de Ejemplo

### 1. Total de pedidos por local
```sql
SELECT 
    local_id,
    COUNT(*) as total_pedidos
FROM pedidos
GROUP BY local_id
ORDER BY total_pedidos DESC;
```

### 2. Ganancias por local
```sql
SELECT 
    local_id,
    COUNT(*) as total_pedidos,
    SUM(costo) as ganancias_totales,
    AVG(costo) as ganancia_promedio
FROM pedidos
GROUP BY local_id
ORDER BY ganancias_totales DESC;
```

### 3. Tiempo promedio por estado
```sql
SELECT 
    estado,
    COUNT(DISTINCT pedido_id) as total_pedidos,
    AVG(
        date_diff('minute', 
            from_iso8601_timestamp(hora_inicio), 
            from_iso8601_timestamp(hora_fin)
        )
    ) as tiempo_promedio_minutos
FROM historial_estados
WHERE hora_inicio IS NOT NULL AND hora_fin IS NOT NULL
GROUP BY estado
ORDER BY tiempo_promedio_minutos DESC;
```

### 4. Pedidos por estado
```sql
SELECT 
    estado,
    COUNT(*) as total
FROM pedidos
GROUP BY estado
ORDER BY total DESC;
```

## Troubleshooting

### Error: "Table not found"
**Solución**: Ejecutar los crawlers
```bash
aws glue start-crawler --name millas-pedidos-crawler
aws glue start-crawler --name millas-historial-crawler
```

Esperar 1-2 minutos y verificar:
```bash
aws glue get-tables --database-name millas_analytics_db
```

### Error: "Column not found"
**Causa**: Los nombres de columnas no coinciden con el schema

**Solución**: Usar los nombres correctos:
- ✅ `hora_inicio`, `hora_fin` (no `timestamp`)
- ✅ `pedido_id`, `estado_id` (no `id`)
- ✅ `local_id` (no `tenant_id` solo)

### Error: "HIVE_CANNOT_OPEN_SPLIT"
**Causa**: Formato de datos incorrecto en S3

**Solución**: 
1. Verificar que los archivos JSON estén bien formados
2. Reexportar datos: `POST /analytics/export`
3. Reejecutar crawlers

## Comandos Útiles

### Ver tablas en Glue
```bash
aws glue get-tables \
    --database-name millas_analytics_db \
    --query 'TableList[*].[Name,StorageDescriptor.Location]' \
    --output table
```

### Ver schema de una tabla
```bash
aws glue get-table \
    --database-name millas_analytics_db \
    --name pedidos \
    --query 'Table.StorageDescriptor.Columns' \
    --output table
```

### Listar archivos en S3
```bash
aws s3 ls s3://bucket-analytic-${AWS_ACCOUNT_ID}/pedidos/
aws s3 ls s3://bucket-analytic-${AWS_ACCOUNT_ID}/historial_estados/
```

### Ver resultados de Athena
```bash
aws s3 ls s3://athena-results-${AWS_ACCOUNT_ID}/results/
```

## Notas Importantes

1. **Workgroup**: Siempre usa `millas-analytics-workgroup`
2. **Database**: Siempre usa `millas_analytics_db`
3. **Formato de fechas**: ISO 8601 (`2024-11-23T10:30:00`)
4. **Productos**: Es un array JSON, usa funciones JSON de Athena para consultarlo

## Ejemplo Completo

```bash
# 1. Exportar datos
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/analytics/export

# 2. Esperar 2 minutos

# 3. Configurar Athena (si es necesario)
cd analytics
bash configure_athena.sh

# 4. Probar query desde consola de Athena
# Workgroup: millas-analytics-workgroup
# Database: millas_analytics_db
# Query: SELECT * FROM pedidos LIMIT 5;

# 5. Usar los endpoints
curl https://your-api.execute-api.us-east-1.amazonaws.com/analytics/pedidos-por-local
```
