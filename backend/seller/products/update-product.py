import json
import boto3
import jwt
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])

SECRET_KEY = os.environ['SECRET_KEY']


# 🔁 Convert Decimal → int (for safety)
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)
    else:
        return obj


# 📦 Standard response
def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,PUT"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    try:
        # 🔐 AUTH
        headers = event.get('headers', {})
        token = headers.get('Authorization') or headers.get('authorization')

        if not token:
            return response(401, {"message": "Unauthorized"})

        token = token.replace("Bearer ", "")
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        seller_id = decoded.get('userId')

        # 📦 BODY
        body = json.loads(event.get('body', '{}'))
        product_id = body.get('productId')

        if not product_id:
            return response(400, {"message": "productId required"})

        # 🔒 CHECK OWNER
        item = table.get_item(Key={"productId": product_id}).get("Item")

        if not item:
            return response(404, {"message": "Product not found"})

        if item.get("sellerId") != seller_id:
            return response(403, {"message": "Forbidden"})

        # 🛠️ BUILD UPDATE (SAFE)
        update_expr = []
        expr_values = {}
        expr_names = {}

        fields = ["name", "price", "discount", "description", "stock", "total", "imageUrl"]

        for field in fields:
            if field in body:
                key_name = f"#{field}"
                value_name = f":{field}"

                update_expr.append(f"{key_name} = {value_name}")
                expr_values[value_name] = body[field]
                expr_names[key_name] = field

        if not update_expr:
            return response(400, {"message": "No fields to update"})

        # 🔥 UPDATE
        table.update_item(
            Key={"productId": product_id},
            UpdateExpression="SET " + ", ".join(update_expr),
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names
        )

        return response(200, {"message": "Product updated successfully"})

    except jwt.ExpiredSignatureError:
        return response(401, {"message": "Token expired"})

    except jwt.InvalidTokenError:
        return response(401, {"message": "Invalid token"})

    except Exception as e:
        print("Update Product Error:", str(e))  # 🔥 CloudWatch log
        return response(500, {"error": str(e)})