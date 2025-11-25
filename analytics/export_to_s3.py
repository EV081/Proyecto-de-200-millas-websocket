import os
import json
import boto3
from datetime import datetime
from decimal import Decimal

# Variables de entorno
TABLE_PEDIDOS = os.environ.get('TABLE_PEDIDOS')
TABLE_HISTORIAL_ESTADOS = os.environ.get('TABLE_HISTORIAL_ESTADOS')
ANALYTICS_BUCKET = os.environ.get('ANALYTICS_BUCKET')

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

def decimal_default(obj):
    """Convierte Decimal a float para JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def export_table_to_s3(table_name, s3_prefix):
    """Exporta una tabla de DynamoDB a S3 en formato JSON"""
    print(f"Exportando tabla {table_name}...")
    
    table = dynamodb.Table(table_name)
    
    # Escanear toda la tabla
    items = []
    response = table.scan()
    items.extend(response.get('Items', []))
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    print(f"Total de items: {len(items)}")
    
    # Generar timestamp para el archivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Guardar en S3
    s3_key = f"{s3_prefix}/data_{timestamp}.json"
    
    # Convertir a JSON
    json_data = json.dumps(items, default=decimal_default, ensure_ascii=False)
    
    # Subir a S3
    s3_client.put_object(
        Bucket=ANALYTICS_BUCKET,
        Key=s3_key,
        Body=json_data,
        ContentType='application/json'
    )
    
    print(f"Exportado a s3://{ANALYTICS_BUCKET}/{s3_key}")
    return s3_key

def lambda_handler(event, context):
    """Handler principal para exportar datos"""
    try:
        print("Iniciando exportación de datos...")
        
        # Exportar tabla de pedidos
        pedidos_key = export_table_to_s3(TABLE_PEDIDOS, 'pedidos')
        
        # Exportar tabla de historial de estados
        historial_key = export_table_to_s3(TABLE_HISTORIAL_ESTADOS, 'historial_estados')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Exportación completada',
                'pedidos': pedidos_key,
                'historial_estados': historial_key
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
