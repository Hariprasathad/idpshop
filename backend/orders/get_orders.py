import os
import boto3
import json
from boto3.dynamodb.conditions import Attr

# Environment variables
ORDERS_TABLE = os.environ.get('ORDERS_TABLE', 'hariprasath-orders')
FRONTEND_URL = os.environ.get('FRONTEND_URL')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(ORDERS_TABLE)

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
        user_id = params.get('userId')
        seller_email = params.get('sellerEmail')
        
        if user_id:
            db_response = table.scan(FilterExpression=Attr('userId').eq(user_id))
        elif seller_email:
            db_response = table.scan(FilterExpression=Attr('sellerEmail').eq(seller_email))
        else:
            return response(400, {'message': 'Missing userId or sellerEmail'})
            
        return response(200, db_response.get('Items', []))
    except Exception as e:
        return response(500, {'message': str(e)})
