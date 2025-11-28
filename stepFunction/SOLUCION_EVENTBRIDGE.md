# 🔧 Solución: EventBridge no invoca el Lambda

## 🔍 Problema Identificado

Los eventos se publican correctamente desde los triggers de empleados, pero el Lambda `cambiarEstado` **NO se está ejecutando**. Esto significa que EventBridge no está invocando el Lambda.

## 📊 Evidencia

- ✅ Los triggers publican eventos correctamente (ves el mensaje "event published")
- ✅ Algunos Lambdas se ejecutan (pedidoEnCocina, cocinaCompleta, empaquetado, delivery)
- ❌ El Lambda `cambiarEstado` NO tiene logs en CloudWatch
- ❌ El Step Function se queda esperando y no avanza

## 🎯 Causa Raíz

El Lambda `cambiarEstado` es el que **recibe los eventos de EventBridge** y envía el `taskToken` al Step Function para que avance. Si este Lambda no se ejecuta, el Step Function nunca avanza.

Posibles causas:
1. **La regla de EventBridge no se creó** durante el deploy
2. **El pattern de la regla no coincide** con los eventos publicados
3. **Falta permisos** para que EventBridge invoque el Lambda
4. **La regla está deshabilitada**

## ✅ Solución Paso a Paso

### Paso 1: Verificar que el servicio esté desplegado

```bash
cd stepFunction
sls info
```

Deberías ver todas las funciones listadas, incluyendo `cambiarEstado`.

### Paso 2: Redesplegar el servicio

Es posible que la regla de EventBridge no se haya creado correctamente:

```bash
cd stepFunction
sls deploy --force
```

Espera a que termine el deploy (puede tomar 2-3 minutos).

### Paso 3: Verificar las reglas de EventBridge

```bash
bash stepFunction/verificar_eventbridge.sh
```

Este script te mostrará:
- Qué reglas de EventBridge existen
- Si están activas
- Qué Lambdas están conectados
- Publicará un evento de prueba

### Paso 4: Verificar logs del Lambda cambiarEstado

```bash
# Ver logs en tiempo real
aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --follow

# O en otra terminal, publica un evento de prueba
python3 stepFunction/test_eventbridge_direct.py e6d2beeb-19c2-4751-861c-de9003f79f7a EnPreparacion
```

Si ves logs del Lambda, significa que EventBridge está funcionando. Si NO ves logs, continúa al siguiente paso.

### Paso 5: Verificar permisos del Lambda

El Lambda necesita permisos para ser invocado por EventBridge. Verifica:

```bash
aws lambda get-policy \
  --function-name service-orders-200-millas-dev-cambiarEstado \
  --region us-east-1
```

Deberías ver una política que permite a `events.amazonaws.com` invocar el Lambda.

### Paso 6: Crear la regla manualmente (si no existe)

Si la regla no se creó automáticamente, créala manualmente:

```bash
# Crear la regla
aws events put-rule \
  --name service-orders-cambiarEstado-rule \
  --event-pattern '{
    "source": ["200millas.cocina", "200millas.delivery", "200millas.cliente"],
    "detail-type": ["EnPreparacion", "CocinaCompleta", "Empaquetado", "PedidoEnCamino", "EntregaDelivery", "ConfirmarPedidoCliente"]
  }' \
  --state ENABLED \
  --region us-east-1

# Obtener el ARN del Lambda
LAMBDA_ARN=$(aws lambda get-function \
  --function-name service-orders-200-millas-dev-cambiarEstado \
  --region us-east-1 \
  --query 'Configuration.FunctionArn' \
  --output text)

# Conectar el Lambda a la regla
aws events put-targets \
  --rule service-orders-cambiarEstado-rule \
  --targets "Id"="1","Arn"="$LAMBDA_ARN" \
  --region us-east-1

# Dar permisos al Lambda
aws lambda add-permission \
  --function-name service-orders-200-millas-dev-cambiarEstado \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:$(aws sts get-caller-identity --query Account --output text):rule/service-orders-cambiarEstado-rule \
  --region us-east-1
```

### Paso 7: Probar el flujo completo

Una vez que hayas verificado que EventBridge funciona:

```bash
# 1. Verificar estado del pedido
bash stepFunction/check_estado_pedido.sh e6d2beeb-19c2-4751-861c-de9003f79f7a

# 2. Ejecutar el flujo completo
bash stepFunction/test_flujo_completo.sh e6d2beeb-19c2-4751-861c-de9003f79f7a
```

## 🐛 Debugging Avanzado

### Ver todos los eventos de EventBridge

```bash
# Habilitar logging de EventBridge (si no está habilitado)
aws events put-rule \
  --name log-all-events \
  --event-pattern '{"source":["200millas.cocina","200millas.delivery","200millas.cliente"]}' \
  --state ENABLED

# Ver eventos en CloudWatch
aws logs tail /aws/events/default --follow
```

### Verificar que los eventos se están publicando

```bash
# Publicar un evento de prueba y verificar
aws events put-events \
  --entries '[{
    "Source": "200millas.cocina",
    "DetailType": "EnPreparacion",
    "Detail": "{\"order_id\": \"TEST-123\", \"empleado_id\": \"EMP-001\", \"status\": \"ACEPTADO\"}",
    "EventBusName": "default"
  }]'

# Inmediatamente después, verificar logs
aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --since 1m
```

## 📝 Checklist de Verificación

- [ ] El servicio stepFunction está desplegado (`sls info`)
- [ ] La función `cambiarEstado` existe en Lambda
- [ ] Existe una regla de EventBridge para `cambiarEstado`
- [ ] La regla está en estado ENABLED
- [ ] La regla tiene el pattern correcto
- [ ] La regla tiene un target (el Lambda)
- [ ] El Lambda tiene permisos para ser invocado por EventBridge
- [ ] Los logs de `cambiarEstado` muestran ejecuciones cuando publicas eventos

## 🎯 Resultado Esperado

Después de aplicar la solución, cuando ejecutes:

```bash
curl -X POST https://YOUR-API/empleados/cocina/iniciar \
  -H "Content-Type: application/json" \
  -d '{"order_id": "e6d2beeb-19c2-4751-861c-de9003f79f7a", "empleado_id": "EMP-001"}'
```

Deberías ver:
1. ✅ Respuesta del trigger: `{"message": "EnPreparacion event published"}`
2. ✅ Logs en `/aws/lambda/service-orders-200-millas-dev-cambiarEstado`
3. ✅ El Step Function avanza al siguiente estado
4. ✅ Nuevo registro en DynamoDB Historial Estados

## 💡 Nota Importante

El problema NO es con los triggers de empleados (esos funcionan bien). El problema es que el Lambda `cambiarEstado` no se está ejecutando cuando EventBridge recibe los eventos.

Una vez que arregles esto, el flujo completo funcionará correctamente.
