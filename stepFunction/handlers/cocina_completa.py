import json
import os
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
TABLE_HISTORIAL_ESTADOS = os.environ['TABLE_HISTORIAL_ESTADOS']
TABLE_PRODUCTOS = os.environ['TABLE_PRODUCTOS']

def handler(event, context):
    print(f"CocinaCompleta Event: {json.dumps(event)}")
    
    task_token = event.get('taskToken')
    input_data = event.get('input', {})
    order_id = input_data.get('order_id')
    empleado_id = input_data.get('empleado_id', 'COCINA')
    
    # Update product inventory
    productos_items = input_data.get('details', {}).get('productos', [])
    if productos_items:
        productos_table = dynamodb.Table(TABLE_PRODUCTOS)
        for item in productos_items:
            producto_id = item.get('producto_id')
            cantidad = item.get('cantidad', 1)
            if producto_id:
                try:
                    # Decrement product quantity
                    productos_table.update_item(
                        Key={'local_id': item.get('local_id', 'default'), 'producto_id': producto_id},
                        UpdateExpression='SET cantidad = cantidad - :val',
                        ExpressionAttributeValues={':val': Decimal(str(cantidad))},
                        ConditionExpression='cantidad >= :val'
                    )
                except Exception as e:
                    print(f"Error updating product {producto_id}: {e}")
    
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
    
    # Save State
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'id_pedido': order_id,
        'createdAt': timestamp,
        'estado': 'cocinando',  # Still in cooking phase, will move to empacando next
        'taskToken': task_token,
        'hora_inicio': timestamp,
        'empleado': empleado_id,
        'details': input_data
    }
    table.put_item(Item=item)
    
    return {
        "status": "COCINA_TERMINADA",
        "order_id": order_id,
        "empleado_id": empleado_id
    }
