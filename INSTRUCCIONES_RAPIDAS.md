# 🚀 Instrucciones Rápidas - 200 Millas

## 🚨 SI TIENES PROBLEMAS AHORA (EventBridge no funciona)

```bash
bash fix_todo.sh <pedido_id>
```

Ejemplo:
```bash
bash fix_todo.sh 9860824a-04f4-4b7d-b65c-abfae2035dd2
```

Este script arregla EventBridge y prueba el flujo completo automáticamente.

---

## Para Desplegar Todo (Primera Vez)

```bash
bash setup_backend.sh
```

Selecciona **opción 1** (Desplegar todo).

El script hará TODO automáticamente:
- ✅ Crea infraestructura (DynamoDB, S3)
- ✅ Genera y puebla datos
- ✅ Despliega microservicios
- ✅ Despliega Step Functions
- ✅ **Configura EventBridge** (NUEVO)
- ✅ Despliega servicio de empleados
- ✅ Despliega analytics
- ✅ Configura Athena

**Tiempo estimado:** 5-7 minutos

---

## Para Probar un Pedido Completo

### 1. Crear un pedido
```bash
curl -X POST https://YOUR-API/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "local_id": "LOCAL-001",
    "usuario_correo": "test@example.com",
    "productos": [{"producto_id": "LOCAL-001#Producto1", "cantidad": 2}],
    "direccion": "Calle Test 123"
  }'
```

Guarda el `pedido_id` que te devuelve.

### 2. Ejecutar el flujo completo automáticamente
```bash
bash stepFunction/test_flujo_completo.sh <pedido_id>
```

Este script ejecutará todos los pasos automáticamente:
- Iniciar cocina
- Completar cocina
- Completar empaquetado
- Iniciar delivery
- Entregar pedido

---

## Para Verificar Estado de un Pedido

```bash
bash stepFunction/check_estado_pedido.sh <pedido_id>
```

Te dirá:
- En qué estado está el pedido
- Cuál es el próximo paso
- El comando exacto que debes ejecutar

---

## Si Algo No Funciona

### Problema: Athena muestra arrays en lugar de filas
```bash
cd analytics
bash fix_and_reexport.sh
```

### Problema: Step Function no avanza
```bash
# 1. Verificar EventBridge
bash stepFunction/verificar_eventbridge.sh

# 2. Si es necesario, arreglar EventBridge
bash stepFunction/fix_eventbridge.sh

# 3. Probar de nuevo
bash stepFunction/test_flujo_completo.sh <pedido_id>
```

### Problema: No sé en qué estado está mi pedido
```bash
bash stepFunction/check_estado_pedido.sh <pedido_id>
```

---

## Endpoints Importantes

### Crear Pedido
```
POST /pedidos
```

### Empleados - Cocina
```
POST /empleados/cocina/iniciar       # Iniciar preparación
POST /empleados/cocina/completar     # Completar cocina
```

### Empleados - Empaque
```
POST /empleados/empaque/completar    # Completar empaquetado
```

### Empleados - Delivery
```
POST /empleados/delivery/iniciar     # Iniciar delivery
POST /empleados/delivery/entregar    # Entregar pedido
```

### Analytics
```
GET /analytics/pedidos-por-local
GET /analytics/ganancias-por-local
GET /analytics/tiempo-pedido
GET /analytics/promedio-por-estado
```

---

## Logs Útiles

```bash
# Ver logs de cambiarEstado (el más importante)
aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --follow

# Ver logs de un estado específico
aws logs tail /aws/lambda/service-orders-200-millas-dev-pedidoEnCocina --follow
aws logs tail /aws/lambda/service-orders-200-millas-dev-cocinaCompleta --follow

# Ver historial de un pedido en DynamoDB
aws dynamodb query \
  --table-name Millas-Historial-Estados \
  --key-condition-expression "pedido_id = :pid" \
  --expression-attribute-values '{":pid":{"S":"<pedido_id>"}}'
```

---

## Orden Correcto de Eventos

```
1. Crear Pedido
   ↓
2. /empleados/cocina/iniciar
   ↓
3. /empleados/cocina/completar
   ↓
4. /empleados/empaque/completar
   ↓
5. /empleados/delivery/iniciar
   ↓
6. /empleados/delivery/entregar
   ↓
✅ COMPLETO
```

**IMPORTANTE:** Debes seguir este orden. No puedes saltar pasos.

---

## Documentación Completa

- `RESUMEN_CAMBIOS.md` - Todos los cambios realizados
- `stepFunction/DIAGNOSTICO_FLUJO.md` - Explicación del flujo
- `stepFunction/SOLUCION_EVENTBRIDGE.md` - Problema de EventBridge
- `analytics/README.md` - Documentación de analytics

---

## ¿Todo Funciona?

Checklist rápido:

- [ ] `bash setup_backend.sh` terminó sin errores
- [ ] Puedes crear un pedido
- [ ] `bash stepFunction/test_flujo_completo.sh <pedido_id>` funciona
- [ ] Athena muestra 40 filas (no 6 arrays)
- [ ] Los endpoints de analytics responden

Si todo está ✅, ¡estás listo! 🎉
