"""
Helper function to update pedido estado in Pedidos table
"""
import os
import boto3

dynamodb = boto3.resource('dynamodb')
TABLE_PEDIDOS = os.environ.get('TABLE_PEDIDOS')

def update_pedido_estado(pedido_id, local_id, nuevo_estado):
    """
    Updates the estado field in the Pedidos table
    
    Args:
        pedido_id: The pedido_id (SK)
        local_id: The local_id (PK)
        nuevo_estado: The new estado value
    """
    if not TABLE_PEDIDOS:
        print("Warning: TABLE_PEDIDOS not configured")
        return False
    
    try:
        table = dynamodb.Table(TABLE_PEDIDOS)
        table.update_item(
            Key={
                'local_id': local_id,
                'pedido_id': pedido_id
            },
            UpdateExpression='SET estado = :estado',
            ExpressionAttributeValues={
                ':estado': nuevo_estado
            }
        )
        print(f"✅ Updated pedido {pedido_id} estado to: {nuevo_estado}")
        return True
    except Exception as e:
        print(f"❌ Error updating pedido estado: {e}")
        return False
