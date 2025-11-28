#!/bin/bash

# Script para verificar la configuración de EventBridge
# Verifica que las reglas estén creadas y conectadas correctamente

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "🔍 Verificando Configuración de EventBridge"
echo "=========================================="
echo ""

# Buscar reglas relacionadas con el servicio
echo -e "${BLUE}📋 Buscando reglas de EventBridge...${NC}"
echo ""

rules=$(aws events list-rules --region us-east-1 --output json | jq -r '.Rules[] | select(.Name | contains("service-orders")) | .Name')

if [ -z "$rules" ]; then
    echo -e "${RED}❌ No se encontraron reglas de EventBridge para service-orders${NC}"
    echo ""
    echo "Esto significa que el servicio no se desplegó correctamente."
    echo "Intenta redesplegar:"
    echo "  cd stepFunction"
    echo "  sls deploy"
    exit 1
fi

echo -e "${GREEN}✅ Reglas encontradas:${NC}"
echo "$rules"
echo ""

# Verificar cada regla
for rule in $rules; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}Regla: ${rule}${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Obtener detalles de la regla
    rule_details=$(aws events describe-rule --name "$rule" --region us-east-1 --output json)
    
    echo "Estado: $(echo "$rule_details" | jq -r '.State')"
    echo "Event Pattern:"
    echo "$rule_details" | jq -r '.EventPattern' | jq '.'
    echo ""
    
    # Obtener targets (lambdas conectadas)
    targets=$(aws events list-targets-by-rule --rule "$rule" --region us-east-1 --output json)
    
    target_count=$(echo "$targets" | jq -r '.Targets | length')
    echo "Targets conectados: ${target_count}"
    
    if [ "$target_count" -gt 0 ]; then
        echo "$targets" | jq -r '.Targets[] | "  - ARN: \(.Arn)\n    ID: \(.Id)"'
    else
        echo -e "${RED}  ⚠️  No hay targets conectados a esta regla${NC}"
    fi
    
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🧪 Probando publicación de evento de prueba...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Publicar un evento de prueba
test_order_id="TEST-$(date +%s)"

echo "Publicando evento EnPreparacion de prueba..."
echo "Order ID: ${test_order_id}"
echo ""

aws events put-events \
    --entries "[
        {
            \"Source\": \"200millas.cocina\",
            \"DetailType\": \"EnPreparacion\",
            \"Detail\": \"{\\\"order_id\\\": \\\"${test_order_id}\\\", \\\"empleado_id\\\": \\\"TEST-EMP\\\", \\\"status\\\": \\\"ACEPTADO\\\"}\",
            \"EventBusName\": \"default\"
        }
    ]" \
    --region us-east-1

echo ""
echo -e "${GREEN}✅ Evento de prueba publicado${NC}"
echo ""
echo "💡 Verifica los logs del Lambda 'cambiar_estado' en CloudWatch:"
echo "   aws logs tail /aws/lambda/service-orders-200-millas-dev-cambiarEstado --follow"
echo ""
echo "Si NO ves logs del evento de prueba, significa que:"
echo "  1. La regla de EventBridge no está activa"
echo "  2. El pattern no coincide con el evento"
echo "  3. El Lambda no tiene permisos para ser invocado por EventBridge"
echo ""
