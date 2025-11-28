#!/bin/bash

# Script de emergencia para arreglar EventBridge y probar

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ORDER_ID="${1:-9860824a-04f4-4b7d-b65c-abfae2035dd2}"

echo "=========================================="
echo "🚨 FIX DE EMERGENCIA"
echo "=========================================="
echo ""
echo "Order ID: ${ORDER_ID}"
echo ""

# Paso 1: Arreglar EventBridge
echo -e "${BLUE}1️⃣  Arreglando EventBridge...${NC}"
cd stepFunction
bash fix_eventbridge.sh
cd ..
echo ""

# Paso 2: Esperar un poco
echo -e "${BLUE}2️⃣  Esperando 5 segundos...${NC}"
sleep 5
echo ""

# Paso 3: Verificar
echo -e "${BLUE}3️⃣  Verificando configuración...${NC}"
cd stepFunction
bash verificar_eventbridge.sh
cd ..
echo ""

# Paso 4: Probar flujo
echo -e "${BLUE}4️⃣  Probando flujo completo...${NC}"
cd stepFunction
bash test_flujo_completo.sh "${ORDER_ID}"
cd ..
echo ""

echo "=========================================="
echo -e "${GREEN}✅ FIX COMPLETADO${NC}"
echo "=========================================="
echo ""
echo "💡 Ahora verifica:"
echo ""
echo "1. Logs del Lambda cambiarEstado:"
echo "   aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --since 5m"
echo ""
echo "2. Estado del Step Function en la consola:"
echo "   https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines"
echo ""
echo "3. Historial en DynamoDB:"
echo "   aws dynamodb query \\"
echo "     --table-name Millas-Historial-Estados \\"
echo "     --key-condition-expression \"pedido_id = :pid\" \\"
echo "     --expression-attribute-values '{\":pid\":{\"S\":\"${ORDER_ID}\"}}'"
echo ""
