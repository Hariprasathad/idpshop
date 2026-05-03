import json
import boto3
import jwt

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
            "Access-Control-Allow-Methods": "OPTIONS,PUT"
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

        # 📦 Get request body
        body = json.loads(event['body'])
        order_id = body.get("orderId")
        new_status = body.get("status")

        if not order_id or not new_status:
            return response(400, {"message": "Missing orderId or status"})

        # 🔄 Update order status
        table.update_item(
            Key={"orderId": order_id},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": new_status}
        )

        return response(200, {"message": "Order status updated"})

    except Exception as e:
        return response(500, {"error": str(e)})