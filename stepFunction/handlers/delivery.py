import json
import os
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from update_pedido_estado import update_pedido_estado

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
TABLE_HISTORIAL_ESTADOS = os.environ['TABLE_HISTORIAL_ESTADOS']
QUEUE_DELIVERY_URL = os.environ['QUEUE_DELIVERY_URL']

def handler(event, context):
    print(f"Delivery Event: {json.dumps(event)}")
    
    task_token = event.get('taskToken')
    input_data = event.get('input', {})
    order_id = input_data.get('order_id')
    empleado_id = input_data.get('empleado_id', 'DELIVERY')
    local_id = input_data.get('details', {}).get('local_id') or input_data.get('local_id', 'UNKNOWN')
    
    # Update Pedidos table
    update_pedido_estado(order_id, local_id, 'pedido_en_camino')
    
    # Enqueue to SQS Delivery
    message_body = {
        "order_id": order_id,
        "action": "DELIVERY",
        "details": input_data
    }
    sqs.send_message(
        QueueUrl=QUEUE_DELIVERY_URL,
        MessageBody=json.dumps(message_body)
    )
    
    # Update previous state's hora_fin
    table = dynamodb.Table(TABLE_HISTORIAL_ESTADOS)
    response = table.query(
        KeyConditionExpression=Key('pedido_id').eq(order_id),
        ScanIndexForward=False,
        Limit=1
    )
    if response.get('Items'):
        prev_item = response['Items'][0]
        table.update_item(
            Key={'pedido_id': order_id, 'estado_id': prev_item['estado_id']},
            UpdateExpression='SET hora_fin = :hf',
            ExpressionAttributeValues={':hf': datetime.utcnow().isoformat()}
        )
    
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'pedido_id': order_id,
        'estado_id': timestamp,
        'createdAt': timestamp,
        'estado': 'enviando',
        'taskToken': task_token,
        'hora_inicio': timestamp,
        'empleado': empleado_id,
        'details': input_data
    }
    table.put_item(Item=item)
    
    return {
        "status": "DELIVERY_EN_CURSO",
        "order_id": order_id,
        "empleado_id": empleado_id
    }
