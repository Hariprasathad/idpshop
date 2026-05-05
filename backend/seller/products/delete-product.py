import json
import boto3
import jwt
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])

SECRET_KEY = os.environ['SECRET_KEY']


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,DELETE"
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

        # 📦 Body
        body = json.loads(event.get('body', '{}'))
        product_id = body.get('productId')

        if not product_id:
            return response(400, {"message": "productId required"})

        # 🔒 Check ownership
        item = table.get_item(Key={"productId": product_id}).get("Item")

        if not item:
            return response(404, {"message": "Product not found"})

        if item.get("sellerId") != seller_id:
            return response(403, {"message": "Forbidden"})

        # 🗑️ Delete item
        table.delete_item(Key={"productId": product_id})

        return response(200, {"message": "Product deleted successfully"})

    except jwt.ExpiredSignatureError:
        return response(401, {"message": "Token expired"})

    except jwt.InvalidTokenError:
        return response(401, {"message": "Invalid token"})

    except Exception as e:
        print(f"Delete Product Error: {str(e)}") # ⭐ Log to CloudWatch
        return response(500, {"error": str(e)})