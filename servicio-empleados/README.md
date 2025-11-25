# Servicio Empleados - API Gateway Endpoints

Este servicio proporciona endpoints API para que los empleados puedan gatillar eventos en el flujo de Step Functions.

## Endpoints Disponibles

### 1. Iniciar Preparación en Cocina
```
POST /empleados/cocina/iniciar
```
**Body:**
```json
{
  "order_id": "uuid-del-pedido",
  "empleado_id": "id-del-empleado"
}
```

### 2. Completar Cocina
```
POST /empleados/cocina/completar
```
**Body:**
```json
{
  "order_id": "uuid-del-pedido",
  "empleado_id": "id-del-empleado"
}
```

### 3. Completar Empaquetado
```
POST /empleados/empaque/completar
```
**Body:**
```json
{
  "order_id": "uuid-del-pedido",
  "empleado_id": "id-del-empleado"
}
```

### 4. Iniciar Delivery
```
POST /empleados/delivery/iniciar
```
**Body:**
```json
{
  "order_id": "uuid-del-pedido",
  "empleado_id": "id-del-empleado"
}
```

### 5. Entregar Pedido
```
POST /empleados/delivery/entregar
```
**Body:**
```json
{
  "order_id": "uuid-del-pedido",
  "empleado_id": "id-del-empleado"
}
```

### 6. Confirmar Recepción del Cliente
```
POST /empleados/cliente/confirmar
```
**Body:**
```json
{
  "order_id": "uuid-del-pedido",
  "empleado_id": "CLIENTE"
}
```

## Despliegue

```bash
cd servicio-empleados
serverless deploy
```

## Eventos Publicados

Cada endpoint publica un evento a EventBridge que es capturado por el Lambda `cambiar_estado` para avanzar el Step Functions:

- `EnPreparacion` → Source: `200millas.cocina`
- `CocinaCompleta` → Source: `200millas.cocina`
- `Empaquetado` → Source: `200millas.cocina`
- `PedidoEnCamino` → Source: `200millas.delivery`
- `EntregaDelivery` → Source: `200millas.delivery`
- `ConfirmarPedidoCliente` → Source: `200millas.cliente`
