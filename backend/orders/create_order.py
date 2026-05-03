import os
import boto3
import json
import uuid
from datetime import datetime

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
        body = json.loads(event.get('body', '{}'))
        item = {
            'orderId': str(uuid.uuid4()),
            'userId': body.get('userId'),
            'productId': body.get('productId'),
            'quantity': body.get('quantity'),
            'sellerEmail': body.get('sellerEmail'),
            'status': 'Pending',
            'timestamp': datetime.now().isoformat()
        }
        table.put_item(Item=item)
        return response(201, {'message': 'Order placed', 'orderId': item['orderId']})
    except Exception as e:
        return response(500, {'message': str(e)})
