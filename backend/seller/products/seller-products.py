import json
import boto3
import jwt
import os
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])

SECRET_KEY = os.environ['SECRET_KEY']


# ✅ Convert Decimal → int (DynamoDB fix)
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
        # 🔐 Get token (case-safe)
        headers = event.get('headers', {})
        token = headers.get('Authorization') or headers.get('authorization')

        if not token:
            return response(401, {"message": "Unauthorized"})

        token = token.replace("Bearer ", "")
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        seller_id = decoded.get('userId')

        # 📦 Query params
        params = event.get('queryStringParameters') or {}

        limit = int(params.get('limit', 10))
        last_key = params.get('lastKey')

        scan_kwargs = {
            "FilterExpression": Attr('sellerId').eq(seller_id),
            "Limit": limit
        }

        # 👉 Pagination support
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = json.loads(last_key)

        res = table.scan(**scan_kwargs)

        items = convert_decimal(res.get('Items', []))

        return response(200, {
            "products": items,
            "lastKey": res.get('LastEvaluatedKey')
        })

    except Exception as e:
        print(f"Seller Products Error: {str(e)}") # ⭐ Log to CloudWatch
        return response(500, {"error": str(e)})