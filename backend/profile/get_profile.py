import json
import boto3
import jwt
import os
from decimal import Decimal

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

users_table = dynamodb.Table(
    os.environ["USERS_TABLE"]
)

SECRET_KEY = os.environ["SECRET_KEY"]


# ============================================
# 🔁 Decimal Convert
# ============================================

def convert_decimal(obj):

    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]

    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}

    elif isinstance(obj, Decimal):
        return int(obj)

    return obj


# ============================================
# 📦 Response
# ============================================

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


# ============================================
# 🚀 Lambda Handler
# ============================================

def lambda_handler(event, context):

    try:

        # ============================================
        # 🔐 JWT AUTH
        # ============================================

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


        # ============================================
        # 👤 GET USER
        # ============================================

        result = users_table.get_item(
            Key={
                "userId": user_id
            }
        )

        user = result.get("Item")


        if not user:

            return response(404, {
                "message": "User not found"
            })


        # ============================================
        # ❌ REMOVE PASSWORD
        # ============================================

        user.pop("password", None)


        # ============================================
        # ✅ SUCCESS
        # ============================================

        return response(200, {

            "profile": convert_decimal(user)

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

        print("Get Profile Error:", str(e))

        return response(500, {
            "error": str(e)
        })