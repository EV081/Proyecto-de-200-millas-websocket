# 🚨 FIX URGENTE - EventBridge No Funciona

## Problema

Los eventos se publican correctamente (ves "event published") pero el Lambda `cambiarEstado` **NO se está ejecutando**. Por eso el Step Function se queda esperando en "ProcesarPedido".

## Solución Inmediata

Ejecuta estos comandos EN ORDEN:

### 1. Arreglar EventBridge

```bash
cd stepFunction
bash fix_eventbridge.sh
cd ..
```

Este script:
- Crea la regla de EventBridge
- Conecta el Lambda `cambiarEstado`
- Configura los permisos

### 2. Verificar que funcionó

```bash
cd stepFunction
bash verificar_eventbridge.sh
cd ..
```

Deberías ver:
- ✅ Reglas encontradas
- ✅ Estado: ENABLED
- ✅ Targets conectados: 1

### 3. Probar con tu pedido

```bash
cd stepFunction
bash test_flujo_completo.sh 9860824a-04f4-4b7d-b65c-abfae2035dd2
cd ..
```

### 4. Verificar logs del Lambda cambiarEstado

```bash
aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --follow
```

En otra terminal, ejecuta el paso 3. Deberías ver logs apareciendo.

---

## ¿Por qué pasó esto?

El `setup_backend.sh` tiene la función `fix_eventbridge_rules()` pero puede que:
1. No se ejecutó correctamente
2. Hubo un error silencioso
3. El Lambda no existía cuando se intentó configurar

## Solución Permanente

Después de arreglar EventBridge manualmente, **redesplega todo** para asegurar que quede bien:

```bash
bash setup_backend.sh
```

Selecciona opción 1 (Desplegar todo).

---

## Verificación Rápida

Ejecuta esto para ver si EventBridge está configurado:

```bash
aws events list-rules --region us-east-1 | grep -i "cambiar\|orders"
```

Si NO ves ninguna regla, EventBridge no está configurado.

---

## Comandos Completos (Copy-Paste)

```bash
# 1. Arreglar EventBridge
cd stepFunction && bash fix_eventbridge.sh && cd ..

# 2. Verificar
cd stepFunction && bash verificar_eventbridge.sh && cd ..

# 3. Probar
cd stepFunction && bash test_flujo_completo.sh 9860824a-04f4-4b7d-b65c-abfae2035dd2 && cd ..

# 4. Ver logs (en otra terminal)
aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --follow
```

---

## Qué Esperar

Después de arreglar EventBridge:

1. **Cuando ejecutes el test_flujo_completo.sh:**
   - ✅ Verás "event published" (como ahora)
   - ✅ **NUEVO:** Verás logs en CloudWatch del Lambda `cambiarEstado`
   - ✅ **NUEVO:** El Step Function avanzará de estado
   - ✅ **NUEVO:** Se crearán registros en DynamoDB Historial Estados

2. **En la consola de Step Functions:**
   - ✅ Verás el flujo avanzar de "ProcesarPedido" → "PedidoEnCocina" → etc.
   - ✅ El estado cambiará de "En progreso" a "Succeeded" al final

3. **En DynamoDB:**
   - ✅ Verás múltiples registros en Millas-Historial-Estados
   - ✅ Cada uno con un estado diferente (procesando, cocinando, empacando, etc.)

---

## Si Aún No Funciona

1. **Verifica que el Lambda existe:**
   ```bash
   aws lambda get-function --function-name service-orders-200-millas-dev-cambiarEstado
   ```

2. **Verifica los logs del Lambda:**
   ```bash
   aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --since 10m
   ```

3. **Publica un evento de prueba manualmente:**
   ```bash
   aws events put-events --entries '[{
     "Source": "200millas.cocina",
     "DetailType": "EnPreparacion",
     "Detail": "{\"order_id\": \"TEST-123\", \"empleado_id\": \"EMP-001\", \"status\": \"ACEPTADO\"}",
     "EventBusName": "default"
   }]'
   ```

4. **Inmediatamente verifica logs:**
   ```bash
   aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --since 1m
   ```

Si NO ves logs, EventBridge no está invocando el Lambda.

---

## Contacto de Emergencia

Si nada funciona, comparte:
1. Output de `bash stepFunction/verificar_eventbridge.sh`
2. Output de `aws lambda get-function --function-name service-orders-200-millas-dev-cambiarEstado`
3. Output de `aws events list-rules --region us-east-1`
