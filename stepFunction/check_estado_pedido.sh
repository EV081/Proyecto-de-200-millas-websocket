#!/bin/bash

# Script para verificar el estado actual de un pedido
# Uso: bash check_estado_pedido.sh <order_id>

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar que se proporcionó el order_id
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Debes proporcionar el order_id${NC}"
    echo ""
    echo "Uso: bash check_estado_pedido.sh <order_id>"
    echo ""
    echo "Ejemplo:"
    echo "  bash check_estado_pedido.sh 927b448d-9400-4355-afe6-9631962f8d35"
    exit 1
fi

ORDER_ID="$1"

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
elif [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

TABLE_HISTORIAL="${TABLE_HISTORIAL_ESTADOS:-Millas-Historial-Estados}"

echo "=========================================="
echo "🔍 Verificando Estado del Pedido"
echo "=========================================="
echo ""
echo "Order ID: ${ORDER_ID}"
echo "Tabla: ${TABLE_HISTORIAL}"
echo ""

# Obtener el último estado del pedido
echo -e "${BLUE}📊 Consultando historial de estados...${NC}"
echo ""

result=$(aws dynamodb query \
    --table-name "${TABLE_HISTORIAL}" \
    --key-condition-expression "pedido_id = :pid" \
    --expression-attribute-values "{\":pid\":{\"S\":\"${ORDER_ID}\"}}" \
    --scan-index-forward false \
    --region us-east-1 \
    --output json)

# Verificar si hay resultados
count=$(echo "$result" | jq -r '.Count')

if [ "$count" -eq 0 ]; then
    echo -e "${RED}❌ No se encontró historial para este pedido${NC}"
    echo ""
    echo "Posibles causas:"
    echo "  1. El order_id es incorrecto"
    echo "  2. El pedido no ha sido creado"
    echo "  3. La tabla de historial está vacía"
    exit 1
fi

echo -e "${GREEN}✅ Se encontraron ${count} estados en el historial${NC}"
echo ""

# Mostrar todos los estados
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 HISTORIAL COMPLETO DE ESTADOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "$result" | jq -r '.Items[] | 
    "Estado: \(.estado.S // "N/A")
    Hora Inicio: \(.hora_inicio.S // "N/A")
    Hora Fin: \(.hora_fin.S // "N/A")
    Empleado: \(.empleado.S // "N/A")
    Task Token: \(if .taskToken.S then "✅ Presente" else "❌ No presente" end)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
'

# Obtener el estado actual (último)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 ESTADO ACTUAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ultimo_estado=$(echo "$result" | jq -r '.Items[0].estado.S // "N/A"')
tiene_token=$(echo "$result" | jq -r '.Items[0].taskToken.S // ""')
hora_inicio=$(echo "$result" | jq -r '.Items[0].hora_inicio.S // "N/A"')
hora_fin=$(echo "$result" | jq -r '.Items[0].hora_fin.S // "N/A"')
empleado=$(echo "$result" | jq -r '.Items[0].empleado.S // "N/A"')

echo "Estado: ${ultimo_estado}"
echo "Hora Inicio: ${hora_inicio}"
echo "Hora Fin: ${hora_fin}"
echo "Empleado: ${empleado}"

if [ -n "$tiene_token" ]; then
    echo -e "Task Token: ${GREEN}✅ Presente (Step Function esperando)${NC}"
else
    echo -e "Task Token: ${YELLOW}❌ No presente (Estado completado)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 PRÓXIMO PASO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Determinar el próximo paso basado en el estado actual
case "$ultimo_estado" in
    "procesando")
        echo "El pedido está en estado inicial."
        echo ""
        echo "Próximo paso:"
        echo "  POST /empleados/cocina/iniciar"
        echo "  Body: {\"order_id\": \"${ORDER_ID}\", \"empleado_id\": \"EMP-001\"}"
        ;;
    "cocinando")
        # Verificar si tiene hora_fin
        if [ "$hora_fin" == "N/A" ] || [ -z "$hora_fin" ]; then
            echo "El pedido está en cocina (preparándose)."
            echo ""
            echo "Próximo paso:"
            echo "  POST /empleados/cocina/completar"
            echo "  Body: {\"order_id\": \"${ORDER_ID}\", \"empleado_id\": \"EMP-001\"}"
        else
            echo "La cocina ha terminado."
            echo ""
            echo "Próximo paso:"
            echo "  POST /empleados/empaque/completar"
            echo "  Body: {\"order_id\": \"${ORDER_ID}\", \"empleado_id\": \"EMP-002\"}"
        fi
        ;;
    "empacando")
        echo "El pedido está siendo empaquetado."
        echo ""
        echo "Próximo paso:"
        echo "  POST /empleados/delivery/iniciar"
        echo "  Body: {\"order_id\": \"${ORDER_ID}\", \"empleado_id\": \"DEL-001\"}"
        ;;
    "enviando")
        echo "El pedido está en camino (delivery)."
        echo ""
        echo "Próximo paso:"
        echo "  POST /empleados/delivery/entregar"
        echo "  Body: {\"order_id\": \"${ORDER_ID}\", \"empleado_id\": \"DEL-001\"}"
        ;;
    "recibido")
        echo -e "${GREEN}✅ El pedido ha sido completado exitosamente${NC}"
        ;;
    *)
        echo "Estado desconocido: ${ultimo_estado}"
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
