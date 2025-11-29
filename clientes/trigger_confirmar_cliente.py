import json
from event_helper import publish_event, response

def handler(event, context):
    """
    Trigger ConfirmarPedidoCliente event
    POST /empleados/cliente/confirmar
    Body: { "order_id": "...", "empleado_id": "..." }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = body.get('order_id')
        empleado_id = body.get('empleado_id', 'CLIENTE')
        
        if not order_id:
            return response(400, {
                'error': 'order_id is required'
            })
        
        detail = {
            'order_id': order_id,
            'empleado_id': empleado_id,
            'status': 'ACEPTADO'
        }
        
        success = publish_event('200millas.cliente', 'ConfirmarPedidoCliente', detail)
        
        if success:
            return response(200, {
                'message': 'ConfirmarPedidoCliente event published',
                'order_id': order_id
            })
        else:
            return response(500, {
                'error': 'Failed to publish event'
            })
    
    except Exception as e:
        return response(500, {
            'error': str(e)
        })
