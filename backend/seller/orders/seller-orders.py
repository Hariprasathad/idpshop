import json
import boto3
import jwt
from boto3.dynamodb.conditions import Attr

# 🔧 DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('hariprasath-orders')

# 🔐 same secret
SECRET_KEY = "your_secret"


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    try:
        # 🔐 JWT check
        token = event['headers'].get('Authorization')
        if not token:
            return response(401, {"message": "Unauthorized"})

        token = token.replace("Bearer ", "")

        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return response(401, {"message": "Token expired"})
        except jwt.InvalidTokenError:
            return response(401, {"message": "Invalid token"})

        seller_email = decoded['email']

        # 📦 Query params (for limit)
        params = event.get('queryStringParameters') or {}
        limit = int(params.get('limit', 0))

        # 🧾 Fetch orders
        result = table.scan(
            FilterExpression=Attr('sellerEmail').eq(seller_email)
        )

        orders = result.get('Items', [])

        # 🔽 Sort latest first (requires createdAt field)
        orders = sorted(
            orders,
            key=lambda x: x.get('createdAt', ''),
            reverse=True
        )

        # 🔢 Apply limit (for recent orders)
        if limit:
            orders = orders[:limit]

        return response(200, orders)

    except Exception as e:
        return response(500, {"error": str(e)})