import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
TABLE_HISTORIAL_ESTADOS = os.environ['TABLE_HISTORIAL_ESTADOS']
QUEUE_COCINA_URL = os.environ['QUEUE_COCINA_URL']

def handler(event, context):
    print(f"ReintentarCocina Event: {json.dumps(event)}")
    
    # This is a Task state (not wait), so event is just the input
    input_data = event.get('input', {})
    order_id = input_data.get('order_id')
    retry_count = input_data.get('retry_count', 0) + 1
    
    # Re-enqueue to SQS Cocina
    message_body = {
        "order_id": order_id,
        "action": "COCINAR_RETRY",
        "retry_count": retry_count,
        "details": input_data
    }
    sqs.send_message(
        QueueUrl=QUEUE_COCINA_URL,
        MessageBody=json.dumps(message_body)
    )
    
    # Log retry
    table = dynamodb.Table(TABLE_HISTORIAL_ESTADOS)
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'id_pedido': order_id,
        'createdAt': timestamp,
        'estado': 'procesando',
        'hora_inicio': timestamp,
        'empleado': 'SYSTEM_RETRY',
        'details': f"Reintento {retry_count} - Re-encolando para cocina"
    }
    table.put_item(Item=item)
    
    return {
        "order_id": order_id,
        "retry_count": retry_count,
        "status": "RETRYING",
        "empleado_id": input_data.get('empleado_id', 'SYSTEM')
    }
