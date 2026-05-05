import json
import boto3
import jwt
import os
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])

SECRET_KEY = os.environ['SECRET_KEY']


# Convert Decimal → int
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)
    else:
        return obj


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
        # 🔐 Auth
        headers = event.get('headers', {})
        token = headers.get('Authorization') or headers.get('authorization')

        if not token:
            return response(401, {"message": "Unauthorized"})

        token = token.replace("Bearer ", "")
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        seller_id = decoded.get('userId')

        # 📦 Fetch orders
        res = orders_table.scan(
            FilterExpression=Attr('sellerId').eq(seller_id)
        )

        orders = convert_decimal(res.get('Items', []))

        # 🟢 Sort by latest (createdAt DESC)
        orders.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

        return response(200, {
            "orders": orders
        })

    except Exception as e:
        print(f"Seller Orders Error: {str(e)}") # ⭐ Log to CloudWatch
        return response(500, {"error": str(e)})