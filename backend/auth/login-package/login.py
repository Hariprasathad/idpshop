import json
import boto3
import time
import jwt
import bcrypt
import os
from boto3.dynamodb.conditions import Key

# Use environment variables
SECRET_KEY = os.environ.get('SECRET_KEY', 'idpshop_secret_key_123')
USERS_TABLE = os.environ.get('USERS_TABLE', 'hariprasath-users')
FRONTEND_URL = os.environ.get('FRONTEND_URL') # No default '*' to prevent CORS/Credentials mismatch

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(USERS_TABLE)

def generate_token(user):
    payload = {
        'userId': user['userId'],
        'role': user['role'],
        'exp': int(time.time()) + (24 * 60 * 60)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

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
        
        if not email or not password:
            return response(400, {'message': 'Missing fields'})

        email = email.lower().strip()
        db_response = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        
        items = db_response.get('Items', [])
        if not items:
            return response(401, {'message': 'Invalid credentials'})
        
        user = items[0]
        if verify_password(password, user['password']):
            token = generate_token(user)
            
            return response(200, {
                'message': 'Login successful',
                'token': token,
                'user': {
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            })

        else:
            return response(401, {'message': 'Invalid credentials'})
    except Exception as e:
        print(str(e))
        return response(500, {'message': 'Internal server error'})

