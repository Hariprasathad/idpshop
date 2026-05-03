import os
import boto3
import json
from boto3.dynamodb.conditions import Key

# Environment variables
REVIEWS_TABLE = os.environ.get('REVIEWS_TABLE', 'hariprasath-reviews')
FRONTEND_URL = os.environ.get('FRONTEND_URL')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(REVIEWS_TABLE)

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
        product_id = params.get('productId')
        if not product_id:
            return response(400, {'message': 'Missing productId'})
            
        db_response = table.query(KeyConditionExpression=Key('productId').eq(product_id))
        return response(200, db_response.get('Items', []))
    except Exception as e:
        return response(500, {'message': str(e)})
