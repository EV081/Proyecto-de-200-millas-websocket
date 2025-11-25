import json
import os
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

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
        KeyConditionExpression=Key('id_pedido').eq(order_id),
        ScanIndexForward=False,
        Limit=1
    )
    if response.get('Items'):
        prev_item = response['Items'][0]
        table.update_item(
            Key={'id_pedido': order_id, 'createdAt': prev_item['createdAt']},
            UpdateExpression='SET hora_fin = :hf',
            ExpressionAttributeValues={':hf': datetime.utcnow().isoformat()}
        )
    
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'id_pedido': order_id,
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
