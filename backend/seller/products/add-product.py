import json
import boto3
import jwt
import uuid
from datetime import datetime

# 🔧 DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('hariprasath-products')

SECRET_KEY = "your_secret"


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
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

        # 📦 Body
        body = json.loads(event['body'])

        product = {
            "productId": str(uuid.uuid4()),  # ✅ correct key
            "name": body.get("name"),
            "price": int(body.get("price", 0)),
            "discount": int(body.get("discount", 0)),
            "description": body.get("description"),
            "stock": int(body.get("stock", 0)),
            "total": int(body.get("total", 0)),
            "imageUrl": body.get("imageUrl"),  # ✅ add this
            "createdAt": datetime.utcnow().isoformat(),  # ✅ auto add
            "sellerEmail": seller_email  # optional (future use)
        }

        # 🔥 Save
        table.put_item(Item=product)

        return response(200, {"message": "Product added successfully"})

    except Exception as e:
        return response(500, {"error": str(e)})