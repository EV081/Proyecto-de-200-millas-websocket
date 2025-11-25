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
    
    results = athena_client.get_query_results(
        QueryExecutionId=query_execution_id
    )
    
    return results

def parse_results(results):
    """Parsea los resultados de Athena a formato JSON"""
    rows = results['ResultSet']['Rows']
    
    if len(rows) < 2:
        return []
    
    headers = [col['VarCharValue'] for col in rows[0]['Data']]
    
    data = []
    for row in rows[1:]:
        row_data = {}
        for i, col in enumerate(row['Data']):
            value = col.get('VarCharValue', None)
            try:
                value = int(value) if value and '.' not in value else float(value)
            except (ValueError, TypeError):
                pass
            row_data[headers[i]] = value
        data.append(row_data)
    
    return data

def lambda_handler(event, context):
    """
    Query: Promedio de tiempo que los pedidos pasan en cada estado
    """
    try:
        # Query SQL que calcula el tiempo promedio en cada estado
        query = """
        WITH tiempos_por_estado AS (
            SELECT 
                pedido_id,
                estado,
                timestamp as inicio,
                LEAD(timestamp) OVER (PARTITION BY pedido_id ORDER BY timestamp) as fin
            FROM historial_estados
        ),
        duraciones AS (
            SELECT 
                estado,
                pedido_id,
                date_diff('minute', 
                    from_iso8601_timestamp(inicio), 
                    from_iso8601_timestamp(fin)
                ) as duracion_minutos
            FROM tiempos_por_estado
            WHERE fin IS NOT NULL
        )
        SELECT 
            estado,
            COUNT(DISTINCT pedido_id) as total_pedidos,
            AVG(duracion_minutos) as tiempo_promedio_minutos,
            MIN(duracion_minutos) as tiempo_minimo_minutos,
            MAX(duracion_minutos) as tiempo_maximo_minutos,
            STDDEV(duracion_minutos) as desviacion_estandar
        FROM duraciones
        GROUP BY estado
        ORDER BY tiempo_promedio_minutos DESC
        """
        
        print("Ejecutando query: Promedio de pedidos por estado")
        results = execute_athena_query(query)
        
        data = parse_results(results)
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'query': 'Promedio de tiempo por estado',
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
