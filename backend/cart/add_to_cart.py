import os
import boto3
import json

# Environment variables
CART_TABLE = os.environ.get('CART_TABLE', 'hariprasath-cart')
FRONTEND_URL = os.environ.get('FRONTEND_URL')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(CART_TABLE)

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
        body = json.loads(event.get('body', '{}'))
        table.put_item(Item={
            'userId': body.get('userId'),
            'productId': body.get('productId'),
            'quantity': body.get('quantity', 1)
        })
        return response(200, {'message': 'Added to cart'})
    except Exception as e:
        return response(500, {'message': str(e)})
