#!/bin/bash

# Script para arreglar la configuración de EventBridge
# Recrea las reglas y permisos necesarios

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "🔧 Arreglando EventBridge"
echo "=========================================="
echo ""

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
elif [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
REGION="us-east-1"
LAMBDA_NAME="service-orders-200-millas-dev-cambiarEstado"
RULE_NAME="service-orders-cambiarEstado-manual"

echo -e "${BLUE}📋 Configuración:${NC}"
echo "   AWS Account: ${AWS_ACCOUNT_ID}"
echo "   Region: ${REGION}"
echo "   Lambda: ${LAMBDA_NAME}"
echo "   Rule: ${RULE_NAME}"
echo ""

# Paso 1: Verificar que el Lambda existe
echo -e "${BLUE}1️⃣  Verificando Lambda...${NC}"
if aws lambda get-function --function-name "${LAMBDA_NAME}" --region "${REGION}" >/dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Lambda existe${NC}"
    LAMBDA_ARN=$(aws lambda get-function \
        --function-name "${LAMBDA_NAME}" \
        --region "${REGION}" \
        --query 'Configuration.FunctionArn' \
        --output text)
    echo "   ARN: ${LAMBDA_ARN}"
else
    echo -e "${RED}   ❌ Lambda no existe${NC}"
    echo ""
    echo "El Lambda debe ser desplegado primero:"
    echo "  cd stepFunction"
    echo "  sls deploy"
    exit 1
fi
echo ""

# Paso 2: Eliminar regla anterior si existe
echo -e "${BLUE}2️⃣  Limpiando reglas anteriores...${NC}"
if aws events describe-rule --name "${RULE_NAME}" --region "${REGION}" >/dev/null 2>&1; then
    echo "   Eliminando targets..."
    aws events remove-targets \
        --rule "${RULE_NAME}" \
        --ids "1" \
        --region "${REGION}" 2>/dev/null || true
    
    echo "   Eliminando regla..."
    aws events delete-rule \
        --name "${RULE_NAME}" \
        --region "${REGION}" 2>/dev/null || true
    
    echo -e "${GREEN}   ✅ Regla anterior eliminada${NC}"
else
    echo "   No hay reglas anteriores"
fi
echo ""

# Paso 3: Crear nueva regla
echo -e "${BLUE}3️⃣  Creando regla de EventBridge...${NC}"

EVENT_PATTERN='{
  "source": ["200millas.cocina", "200millas.delivery", "200millas.cliente"],
  "detail-type": ["EnPreparacion", "CocinaCompleta", "Empaquetado", "PedidoEnCamino", "EntregaDelivery", "ConfirmarPedidoCliente"]
}'

aws events put-rule \
    --name "${RULE_NAME}" \
    --event-pattern "${EVENT_PATTERN}" \
    --state ENABLED \
    --description "Rule to trigger cambiarEstado Lambda for order state changes" \
    --region "${REGION}"

echo -e "${GREEN}   ✅ Regla creada${NC}"
echo ""

# Paso 4: Conectar Lambda a la regla
echo -e "${BLUE}4️⃣  Conectando Lambda a la regla...${NC}"

aws events put-targets \
    --rule "${RULE_NAME}" \
    --targets "Id"="1","Arn"="${LAMBDA_ARN}" \
    --region "${REGION}"

echo -e "${GREEN}   ✅ Lambda conectado${NC}"
echo ""

# Paso 5: Dar permisos al Lambda
echo -e "${BLUE}5️⃣  Configurando permisos...${NC}"

# Eliminar permiso anterior si existe
aws lambda remove-permission \
    --function-name "${LAMBDA_NAME}" \
    --statement-id AllowEventBridgeInvokeManual \
    --region "${REGION}" 2>/dev/null || true

# Agregar nuevo permiso
RULE_ARN="arn:aws:events:${REGION}:${AWS_ACCOUNT_ID}:rule/${RULE_NAME}"

aws lambda add-permission \
    --function-name "${LAMBDA_NAME}" \
    --statement-id AllowEventBridgeInvokeManual \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn "${RULE_ARN}" \
    --region "${REGION}"

echo -e "${GREEN}   ✅ Permisos configurados${NC}"
echo ""

# Paso 6: Verificar configuración
echo -e "${BLUE}6️⃣  Verificando configuración...${NC}"

rule_state=$(aws events describe-rule --name "${RULE_NAME}" --region "${REGION}" --query 'State' --output text)
echo "   Estado de la regla: ${rule_state}"

targets_count=$(aws events list-targets-by-rule --rule "${RULE_NAME}" --region "${REGION}" --query 'length(Targets)' --output text)
echo "   Targets conectados: ${targets_count}"

if [ "${rule_state}" == "ENABLED" ] && [ "${targets_count}" -gt 0 ]; then
    echo -e "${GREEN}   ✅ Configuración correcta${NC}"
else
    echo -e "${RED}   ⚠️  Configuración incompleta${NC}"
fi
echo ""

# Paso 7: Publicar evento de prueba
echo -e "${BLUE}7️⃣  Publicando evento de prueba...${NC}"

TEST_ORDER_ID="TEST-$(date +%s)"

aws events put-events \
    --entries "[
        {
            \"Source\": \"200millas.cocina\",
            \"DetailType\": \"EnPreparacion\",
            \"Detail\": \"{\\\"order_id\\\": \\\"${TEST_ORDER_ID}\\\", \\\"empleado_id\\\": \\\"TEST-EMP\\\", \\\"status\\\": \\\"ACEPTADO\\\"}\",
            \"EventBusName\": \"default\"
        }
    ]" \
    --region "${REGION}"

echo -e "${GREEN}   ✅ Evento de prueba publicado${NC}"
echo "   Order ID: ${TEST_ORDER_ID}"
echo ""

echo "⏳ Esperando 5 segundos para que el Lambda se ejecute..."
sleep 5
echo ""

# Paso 8: Verificar logs
echo -e "${BLUE}8️⃣  Verificando logs del Lambda...${NC}"

LOG_GROUP="/aws/lambda/${LAMBDA_NAME}"

if aws logs describe-log-streams \
    --log-group-name "${LOG_GROUP}" \
    --order-by LastEventTime \
    --descending \
    --limit 1 \
    --region "${REGION}" >/dev/null 2>&1; then
    
    echo "   Últimos logs:"
    aws logs tail "${LOG_GROUP}" --since 1m --region "${REGION}" 2>/dev/null || echo "   (No hay logs recientes)"
else
    echo -e "${YELLOW}   ⚠️  No se encontraron logs${NC}"
    echo "   Esto puede significar que el Lambda no se ha ejecutado aún"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ Configuración Completada${NC}"
echo "=========================================="
echo ""
echo "💡 Próximos pasos:"
echo ""
echo "1. Verifica que el Lambda se ejecutó:"
echo "   aws logs tail ${LOG_GROUP} --follow"
echo ""
echo "2. Prueba con un pedido real:"
echo "   bash stepFunction/test_flujo_completo.sh <order_id>"
echo ""
echo "3. Si aún no funciona, verifica el deploy:"
echo "   cd stepFunction"
echo "   sls deploy --force"
echo ""
