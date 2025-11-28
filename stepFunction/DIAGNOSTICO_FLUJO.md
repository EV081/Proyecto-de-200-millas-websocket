# 🔍 Diagnóstico del Flujo de Step Functions

## Problema Identificado

El Step Function se queda "En progreso" y no avanza cuando llamas a los triggers de empleados.

## Causa Raíz

El flujo tiene **múltiples estados con `waitForTaskToken`** y cada uno espera un evento específico:

```
1. ProcesarPedido (waitForTaskToken) 
   ↓ (evento: CrearPedido - automático)
   
2. PedidoEnCocina (waitForTaskToken) 
   ↓ (evento: EnPreparacion - manual)
   
3. EvaluarCocina (Choice)
   ↓
   
4. CocinaCompleta (waitForTaskToken)
   ↓ (evento: CocinaCompleta - manual)
   
5. Empaquetado (waitForTaskToken)
   ↓ (evento: Empaquetado - manual)
   
6. Delivery (waitForTaskToken)
   ↓ (evento: PedidoEnCamino - manual)
   
7. EvaluarDelivery (Choice)
   ↓
   
8. Entregado (waitForTaskToken)
   ↓ (evento: EntregaDelivery - manual)
   
9. EntregaCompleta (Task final)
```

## Flujo Correcto de Eventos

Para que un pedido avance completamente, debes llamar a los endpoints EN ORDEN:

### 1. Crear Pedido
```bash
POST /pedidos
```
→ Step Function inicia y se queda esperando en **PedidoEnCocina**

### 2. Iniciar Preparación en Cocina
```bash
POST /empleados/cocina/iniciar
Body: { "order_id": "xxx", "empleado_id": "EMP-001" }
```
→ Publica evento `EnPreparacion`
→ Step Function avanza de **PedidoEnCocina** → **CocinaCompleta**
→ Se queda esperando en **CocinaCompleta**

### 3. Completar Cocina
```bash
POST /empleados/cocina/completar
Body: { "order_id": "xxx", "empleado_id": "EMP-001" }
```
→ Publica evento `CocinaCompleta`
→ Step Function avanza de **CocinaCompleta** → **Empaquetado**
→ Se queda esperando en **Empaquetado**

### 4. Completar Empaquetado
```bash
POST /empleados/empaque/completar
Body: { "order_id": "xxx", "empleado_id": "EMP-002" }
```
→ Publica evento `Empaquetado`
→ Step Function avanza de **Empaquetado** → **Delivery**
→ Se queda esperando en **Delivery**

### 5. Iniciar Delivery
```bash
POST /empleados/delivery/iniciar
Body: { "order_id": "xxx", "empleado_id": "DEL-001" }
```
→ Publica evento `PedidoEnCamino`
→ Step Function avanza de **Delivery** → **Entregado**
→ Se queda esperando en **Entregado**

### 6. Entregar Pedido
```bash
POST /empleados/delivery/entregar
Body: { "order_id": "xxx", "empleado_id": "DEL-001" }
```
→ Publica evento `EntregaDelivery`
→ Step Function avanza de **Entregado** → **EntregaCompleta**
→ **FINALIZA** ✅

## Cómo Verificar en Qué Estado Está

### Opción 1: Consola de Step Functions
1. Ve a AWS Step Functions
2. Busca tu ejecución (Order-xxx)
3. En el diagrama visual verás en qué estado está esperando (color azul)

### Opción 2: DynamoDB
```bash
aws dynamodb query \
  --table-name Millas-Historial-Estados \
  --key-condition-expression "pedido_id = :pid" \
  --expression-attribute-values '{":pid":{"S":"tu-order-id"}}' \
  --scan-index-forward false \
  --limit 1
```

El último registro te dirá en qué estado está y tendrá el `taskToken` que está esperando.

## Solución Rápida

Si tu Step Function está en **PedidoEnCocina** (después de crear el pedido), debes llamar PRIMERO a:

```bash
POST /empleados/cocina/iniciar
Body: { "order_id": "927b448d-9400-4355-afe6-9631962f8d35", "empleado_id": "EMP-001" }
```

NO llames directamente a `/empleados/cocina/completar` porque ese evento es para el siguiente estado.

## Script de Prueba Completo

```bash
#!/bin/bash

# 1. Crear pedido
ORDER_RESPONSE=$(curl -X POST https://YOUR-API/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "local_id": "LOCAL-001",
    "usuario_correo": "test@example.com",
    "productos": [{"producto_id": "PROD-001", "cantidad": 2}],
    "direccion": "Calle Test 123"
  }')

ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.pedido_id')
echo "Pedido creado: $ORDER_ID"
sleep 2

# 2. Iniciar cocina
curl -X POST https://YOUR-API/empleados/cocina/iniciar \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$ORDER_ID\", \"empleado_id\": \"EMP-001\"}"
sleep 2

# 3. Completar cocina
curl -X POST https://YOUR-API/empleados/cocina/completar \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$ORDER_ID\", \"empleado_id\": \"EMP-001\"}"
sleep 2

# 4. Completar empaquetado
curl -X POST https://YOUR-API/empleados/empaque/completar \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$ORDER_ID\", \"empleado_id\": \"EMP-002\"}"
sleep 2

# 5. Iniciar delivery
curl -X POST https://YOUR-API/empleados/delivery/iniciar \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$ORDER_ID\", \"empleado_id\": \"DEL-001\"}"
sleep 2

# 6. Entregar pedido
curl -X POST https://YOUR-API/empleados/delivery/entregar \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$ORDER_ID\", \"empleado_id\": \"DEL-001\"}"

echo "Flujo completo ejecutado para pedido: $ORDER_ID"
```
