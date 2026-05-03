import os
import boto3
import json
from datetime import datetime

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
        body = json.loads(event.get('body', '{}'))
        table.put_item(Item={
            'productId': body.get('productId'),
            'userId': body.get('userId'),
            'rating': body.get('rating'),
            'comment': body.get('comment'),
            'timestamp': datetime.now().isoformat()
        })
        return response(201, {'message': 'Review added'})
    except Exception as e:
        return response(500, {'message': str(e)})
