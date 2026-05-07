import json
import boto3
import jwt
import os

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

cart_table = dynamodb.Table(
    os.environ["CART_TABLE"]
)

SECRET_KEY = os.environ["SECRET_KEY"]


# ============================================
# 📦 Response
# ============================================

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


# ============================================
# 🚀 Lambda Handler
# ============================================

def lambda_handler(event, context):

    try:

        # 🔐 JWT
        headers = event.get("headers", {})

        token = headers.get("Authorization") or headers.get("authorization")

        if not token:

            return response(401, {
                "message": "Unauthorized"
            })

        token = token.replace("Bearer ", "")

        decoded = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        user_id = decoded.get("userId")


        # 📦 Body
        body = json.loads(event.get("body", "{}"))

        product_id = body.get("productId")


        if not product_id:

            return response(400, {
                "message": "productId required"
            })


        # 🗑️ Delete Item
        cart_table.delete_item(
            Key={
                "userId": user_id,
                "productId": product_id
            }
        )


        return response(200, {

            "message": "Removed from cart"

        })


    except jwt.ExpiredSignatureError:

        return response(401, {
            "message": "Token expired"
        })


    except jwt.InvalidTokenError:

        return response(401, {
            "message": "Invalid token"
        })


    except Exception as e:

        print("Remove Cart Error:", str(e))

        return response(500, {
            "error": str(e)
        })