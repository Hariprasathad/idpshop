import os
import boto3
import json
import uuid
from datetime import datetime

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
        body = json.loads(event.get('body', '{}'))
        item = {
            'productId': str(uuid.uuid4()),
            'name': body.get('name'),
            'description': body.get('description'),
            'price': body.get('price'),
            'discount': body.get('discount', 0),
            'stock': body.get('stock'),
            'imageUrl': body.get('imageUrl'),
            'sellerEmail': body.get('sellerEmail'),
            'totalProduct': body.get('totalProduct', 0),
            'createdAt': datetime.now().isoformat()
        }
        table.put_item(Item=item)
        return response(201, {'message': 'Product created', 'productId': item['productId']})
    except Exception as e:
        return response(500, {'message': str(e)})
