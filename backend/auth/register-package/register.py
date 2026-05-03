import json
import boto3
import bcrypt
import os
import uuid
from boto3.dynamodb.conditions import Attr, Key

# Environment variables
USERS_TABLE = os.environ.get('USERS_TABLE', 'hariprasath-users')
FRONTEND_URL = os.environ.get('FRONTEND_URL')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(USERS_TABLE)


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': FRONTEND_URL if FRONTEND_URL else '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))

        email = body.get('email')
        password = body.get('password')
        name = body.get('name')
        role = body.get('role', 'user')

        # 🔥 Validate input
        if not email or not password or not name:
            return response(400, {'message': 'Missing required fields'})

        # 🔥 Normalize email
        email = email.lower().strip()

        # 🔍 Check if user exists (GSI: email-index)
        check_response = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )

        if check_response.get('Items'):
            return response(400, {'message': 'User already exists'})

        # 🛑 Only one seller allowed
        if role == 'seller':
            existing_seller = table.scan(
                FilterExpression=Attr('role').eq('seller')
            )
            if existing_seller.get('Items'):
                return response(400, {'message': 'A seller account already exists.'})

        # 🆔 Generate userId (Primary Key)
        user_id = str(uuid.uuid4())

        # 💾 Save user
        table.put_item(Item={
            'userId': user_id,
            'email': email,
            'password': hash_password(password),
            'name': name,
            'role': role
        })

        return response(201, {'message': 'User registered successfully'})

    except Exception as e:
        print(str(e))
        return response(500, {'message': 'Internal server error'})