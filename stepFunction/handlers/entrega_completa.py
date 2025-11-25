import json
import os
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
events = boto3.client('events')
TABLE_HISTORIAL_ESTADOS = os.environ['TABLE_HISTORIAL_ESTADOS']
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')

def handler(event, context):
    print(f"EntregaCompleta Event: {json.dumps(event)}")
    
    input_data = event.get('input', {})
    order_id = input_data.get('order_id')
    empleado_id = input_data.get('empleado_id', 'SYSTEM')
    
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
    
    # Save final state
    timestamp = datetime.utcnow().isoformat()
    item = {
        'id_pedido': order_id,
        'createdAt': timestamp,
        'estado': 'recibido',
        'hora_inicio': timestamp,
        'hora_fin': timestamp,
        'empleado': empleado_id,
        'details': 'Pedido completado exitosamente'
    }
    table.put_item(Item=item)
    
    # Publish CorreoAgradecimiento event to EventBridge
    try:
        events.put_events(
            Entries=[{
                'Source': '200millas.pedidos',
                'DetailType': 'CorreoAgradecimiento',
                'Detail': json.dumps({
                    'order_id': order_id,
                    'timestamp': timestamp,
                    'message': 'Gracias por tu pedido'
                }),
                'EventBusName': EVENT_BUS_NAME
            }]
        )
        print(f"Published CorreoAgradecimiento event for order {order_id}")
    except Exception as e:
        print(f"Error publishing event: {e}")
    
    return {
        "status": "COMPLETED",
        "order_id": order_id,
        "message": "Pedido completado y email enviado"
    }
