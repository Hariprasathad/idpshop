import os
import boto3
import json

# Environment variables
PRODUCTS_TABLE = os.environ.get('PRODUCTS_TABLE', 'hariprasath-products')
FRONTEND_URL = os.environ.get('FRONTEND_URL')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(PRODUCTS_TABLE)

def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': FRONTEND_URL,
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE',
            'Access-Control-Allow-Credentials': 'true',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }

def lambda_handler(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        query = params.get('q', '').lower()
        if not query:
            return response(200, [])
            
        db_response = table.scan()
        items = db_response.get('Items', [])
        
        filtered = [
            i for i in items 
            if query in i.get('name', '').lower() or query in i.get('description', '').lower()
        ]
        
        return response(200, filtered)
    except Exception as e:
        return response(500, {'message': str(e)})
