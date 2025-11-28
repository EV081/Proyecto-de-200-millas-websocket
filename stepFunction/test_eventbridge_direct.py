#!/usr/bin/env python3
"""
Script para probar EventBridge directamente
Publica un evento y verifica si el Lambda se ejecuta
"""

import boto3
import json
import time
from datetime import datetime

events_client = boto3.client('events', region_name='us-east-1')
logs_client = boto3.client('logs', region_name='us-east-1')

def publish_test_event(order_id, event_type='EnPreparacion'):
    """Publica un evento de prueba"""
    
    source_map = {
        'EnPreparacion': '200millas.cocina',
        'CocinaCompleta': '200millas.cocina',
        'Empaquetado': '200millas.cocina',
        'PedidoEnCamino': '200millas.delivery',
        'EntregaDelivery': '200millas.delivery',
        'ConfirmarPedidoCliente': '200millas.cliente'
    }
    
    source = source_map.get(event_type, '200millas.cocina')
    
    detail = {
        'order_id': order_id,
        'empleado_id': 'TEST-EMPLEADO',
        'status': 'ACEPTADO',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print(f"📤 Publicando evento:")
    print(f"   Source: {source}")
    print(f"   DetailType: {event_type}")
    print(f"   Detail: {json.dumps(detail, indent=2)}")
    print()
    
    response = events_client.put_events(
        Entries=[
            {
                'Source': source,
                'DetailType': event_type,
                'Detail': json.dumps(detail),
                'EventBusName': 'default'
            }
        ]
    )
    
    print(f"✅ Evento publicado")
    print(f"   Response: {json.dumps(response, indent=2, default=str)}")
    print()
    
    return response

def check_lambda_logs(log_group_name='/aws/lambda/service-orders-200-millas-dev-cambiarEstado', seconds=10):
    """Verifica los logs del Lambda"""
    
    print(f"🔍 Verificando logs de {log_group_name}...")
    print(f"   Esperando {seconds} segundos...")
    time.sleep(seconds)
    
    try:
        # Obtener streams recientes
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not streams_response.get('logStreams'):
            print(f"❌ No se encontraron log streams en {log_group_name}")
            return
        
        print(f"✅ Se encontraron {len(streams_response['logStreams'])} log streams")
        print()
        
        # Leer los últimos eventos
        for stream in streams_response['logStreams'][:2]:
            stream_name = stream['logStreamName']
            print(f"📋 Stream: {stream_name}")
            print(f"   Último evento: {stream.get('lastEventTime', 'N/A')}")
            
            try:
                events_response = logs_client.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=stream_name,
                    limit=50,
                    startFromHead=False
                )
                
                events = events_response.get('events', [])
                if events:
                    print(f"   Eventos recientes:")
                    for event in events[-10:]:  # Últimos 10 eventos
                        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                        message = event['message'].strip()
                        print(f"     [{timestamp}] {message}")
                else:
                    print(f"   No hay eventos recientes")
                    
            except Exception as e:
                print(f"   Error leyendo eventos: {e}")
            
            print()
            
    except logs_client.exceptions.ResourceNotFoundException:
        print(f"❌ Log group {log_group_name} no existe")
        print(f"   Esto significa que el Lambda nunca se ha ejecutado")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python3 test_eventbridge_direct.py <order_id> [event_type]")
        print()
        print("Ejemplo:")
        print("  python3 test_eventbridge_direct.py e6d2beeb-19c2-4751-861c-de9003f79f7a EnPreparacion")
        print()
        print("Tipos de eventos disponibles:")
        print("  - EnPreparacion")
        print("  - CocinaCompleta")
        print("  - Empaquetado")
        print("  - PedidoEnCamino")
        print("  - EntregaDelivery")
        print("  - ConfirmarPedidoCliente")
        sys.exit(1)
    
    order_id = sys.argv[1]
    event_type = sys.argv[2] if len(sys.argv) > 2 else 'EnPreparacion'
    
    print("=" * 60)
    print("🧪 Test de EventBridge")
    print("=" * 60)
    print()
    
    # Publicar evento
    publish_test_event(order_id, event_type)
    
    # Verificar logs
    check_lambda_logs()
    
    print("=" * 60)
    print("✅ Test completado")
    print("=" * 60)
    print()
    print("💡 Si NO ves logs del Lambda 'cambiarEstado', verifica:")
    print("   1. Que la regla de EventBridge esté activa")
    print("   2. Que el pattern coincida con el evento")
    print("   3. Que el Lambda tenga permisos")
    print()
    print("   Ejecuta: bash stepFunction/verificar_eventbridge.sh")
    print()

if __name__ == '__main__':
    main()
