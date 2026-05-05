import json
import boto3
import jwt
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['ORDERS_TABLE'])

SECRET_KEY = os.environ['SECRET_KEY']


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

        order_id = body.get("orderId")
        new_status = body.get("status")

        if not order_id or not new_status:
            return response(400, {"message": "orderId and status required"})

        # 🔒 Allowed statuses
        allowed_status = ["Processing", "Shipped", "Delivered"]

        if new_status not in allowed_status:
            return response(400, {"message": "Invalid status value"})

        # 🔍 Check order exists
        item = table.get_item(Key={"orderId": order_id}).get("Item")

        if not item:
            return response(404, {"message": "Order not found"})

        # 🔒 Check ownership (IMPORTANT)
        if item.get("sellerId") != seller_id:
            return response(403, {"message": "Forbidden"})

        # 🔄 Update
        table.update_item(
            Key={"orderId": order_id},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": new_status}
        )

        return response(200, {"message": "Order status updated successfully"})

    except jwt.ExpiredSignatureError:
        return response(401, {"message": "Token expired"})

    except jwt.InvalidTokenError:
        return response(401, {"message": "Invalid token"})

    except Exception as e:
        print(f"Update Order Status Error: {str(e)}") # ⭐ Log to CloudWatch
        return response(500, {"error": str(e)})