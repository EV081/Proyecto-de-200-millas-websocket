import os
import json
import boto3
import time

GLUE_DATABASE = os.environ.get('GLUE_DATABASE')
ATHENA_OUTPUT_BUCKET = os.environ.get('ATHENA_OUTPUT_BUCKET')

athena_client = boto3.client('athena')

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,OPTIONS"
}

def execute_athena_query(query):
    """Ejecuta una query en Athena y espera los resultados"""
    
    # Iniciar la query
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': GLUE_DATABASE
        },
        ResultConfiguration={
            'OutputLocation': f's3://{ATHENA_OUTPUT_BUCKET}/'
        }
    )
    
    query_execution_id = response['QueryExecutionId']
    print(f"Query ID: {query_execution_id}")
    
    # Esperar a que termine
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        query_status = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        
        status = query_status['QueryExecution']['Status']['State']
        
        if status == 'SUCCEEDED':
            break
        elif status in ['FAILED', 'CANCELLED']:
            reason = query_status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
            raise Exception(f"Query failed: {reason}")
        
        time.sleep(2)
        attempt += 1
    
    if attempt >= max_attempts:
        raise Exception("Query timeout")
    
    # Obtener resultados
    results = athena_client.get_query_results(
        QueryExecutionId=query_execution_id
    )
    
    return results

def parse_results(results):
    """Parsea los resultados de Athena a formato JSON"""
    rows = results['ResultSet']['Rows']
    
    if len(rows) < 2:
        return []
    
    # Primera fila son los headers
    headers = [col['VarCharValue'] for col in rows[0]['Data']]
    
    # Resto son los datos
    data = []
    for row in rows[1:]:
        row_data = {}
        for i, col in enumerate(row['Data']):
            value = col.get('VarCharValue', None)
            # Intentar convertir a número si es posible
            try:
                value = int(value) if value and '.' not in value else float(value)
            except (ValueError, TypeError):
                pass
            row_data[headers[i]] = value
        data.append(row_data)
    
    return data

def lambda_handler(event, context):
    """
    Query: Total de pedidos por local
    """
    try:
        # Query SQL
        query = """
        SELECT 
            local_id,
            COUNT(*) as total_pedidos
        FROM pedidos
        GROUP BY local_id
        ORDER BY total_pedidos DESC
        """
        
        print("Ejecutando query: Total de pedidos por local")
        results = execute_athena_query(query)
        
        # Parsear resultados
        data = parse_results(results)
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'query': 'Total de pedidos por local',
                'data': data
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': str(e)
            })
        }
