import json
import boto3
import jwt
import os
import uuid
from datetime import datetime
from decimal import Decimal

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

wishlist_table = dynamodb.Table(
    os.environ["WISHLIST_TABLE"]
)

products_table = dynamodb.Table(
    os.environ["PRODUCTS_TABLE"]
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
            "Access-Control-Allow-Methods": "OPTIONS,POST"
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


        # 🔍 Check Duplicate (Toggle Behavior)
        existing = wishlist_table.scan(
            FilterExpression="userId = :uid AND productId = :pid",
            ExpressionAttributeValues={
                ":uid": user_id,
                ":pid": product_id
            }
        ).get("Items", [])

        if existing:
            # Remove if exists
            wishlist_table.delete_item(Key={"wishlistId": existing[0]["wishlistId"]})
            return response(200, {"message": "Removed from wishlist", "action": "removed"})

        # 🛑 Limit Check (Max 10)
        current_wishlist = wishlist_table.scan(
            FilterExpression="userId = :uid",
            ExpressionAttributeValues={":uid": user_id},
            Select="COUNT"
        )
        if current_wishlist.get("Count", 0) >= 10:
            return response(400, {
                "message": "Wishlist limit reached (Max 10 items allowed)"
            })

        # 🔍 Product Exists
        product = products_table.get_item(Key={"productId": product_id}).get("Item")
        if not product:
            return response(404, {"message": "Product not found"})

        # 💾 Save Wishlist
        wishlist_item = {
            "wishlistId": str(uuid.uuid4()),
            "userId": user_id,
            "productId": product_id,
            "name": product.get("name"),
            "imageUrl": product.get("imageUrl"),
            "price": product.get("price"),
            "discount": product.get("discount"),
            "createdAt": datetime.utcnow().isoformat()
        }

        wishlist_table.put_item(Item=wishlist_item)

        return response(201, {
            "message": "Added to wishlist",
            "action": "added",
            "wishlist": convert_decimal(wishlist_item)
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

        print("Wishlist Error:", str(e))

        return response(500, {
            "error": str(e)
        })