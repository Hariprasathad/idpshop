import json
import boto3
import jwt
import os
from decimal import Decimal

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

orders_table = dynamodb.Table(
    os.environ["ORDERS_TABLE"]
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
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
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
        # 📦 GET USER ORDERS
        # ============================================

        result = orders_table.scan(
            FilterExpression="userId = :uid",
            ExpressionAttributeValues={
                ":uid": user_id
            }
        )

        orders = result.get("Items", [])


        # ============================================
        # 📦 SORT LATEST FIRST
        # ============================================

        orders.sort(
            key=lambda x: x.get("createdAt", ""),
            reverse=True
        )


        # ============================================
        # 📦 CHECK REVIEWS
        # ============================================
        reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])
        
        for order in orders:
            # Check if user reviewed THIS product
            review_check = reviews_table.scan(
                FilterExpression="userId = :uid AND productId = :pid",
                ExpressionAttributeValues={
                    ":uid": user_id,
                    ":pid": order.get("productId")
                }
            )
            order["reviewed"] = review_check.get("Count", 0) > 0


        # ============================================
        # ✅ SUCCESS
        # ============================================

        return response(200, {

            "orders": convert_decimal(orders),

            "count": len(orders)

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

        print("Get My Orders Error:", str(e))

        return response(500, {
            "error": str(e)
        })