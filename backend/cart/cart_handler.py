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

cart_table = dynamodb.Table(
    os.environ["CART_TABLE"]
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
        return {
            k: convert_decimal(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    elif isinstance(obj, str) and "hariprasath-product-images.s3" in obj:
        # Smart Rewrite: Prevent double "/images/images/" paths
        parts = obj.split("amazonaws.com/")
        if len(parts) > 1:
            key = parts[1]
            if key.startswith("images/"):
                key = key[7:] # Strip leading "images/"
            return f"https://d3r1l4tg7odjwk.cloudfront.net/images/{key}"

    return obj

# ============================================
# 📦 Response
# ============================================

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers":
            "Content-Type,Authorization",
            "Access-Control-Allow-Methods":
            "OPTIONS,GET,POST,DELETE"
        },
        "body": json.dumps(body)
    }

# ============================================
# 🔐 JWT AUTH
# ============================================

def get_user_id(event):
    headers = event.get("headers", {})

    token = (
        headers.get("Authorization")
        or
        headers.get("authorization")
    )

    if not token:
        return None

    token = token.replace("Bearer ", "")

    decoded = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=["HS256"]
    )

    return decoded.get("userId")

# ============================================
# 🚀 Lambda Handler
# ============================================

def lambda_handler(event, context):
    try:
        # ============================================
        # 🔐 AUTH
        # ============================================

        user_id = get_user_id(event)

        if not user_id:
            return response(401, {
                "message": "Unauthorized"
            })

        # ============================================
        # 🌐 METHOD
        # ============================================

        # ============================================
        # 🌐 METHOD (Robust Extraction)
        # ============================================
        method = event.get("httpMethod")
        if not method:
            method = event.get("requestContext", {}).get("http", {}).get("method")

        # ============================================
        # 📦 GET CART
        # ============================================

        if method == "GET":
            result = cart_table.scan(
                FilterExpression=
                "userId = :uid",
                ExpressionAttributeValues={
                    ":uid": user_id
                }
            )

            items = result.get("Items", [])

            return response(200, {
                "cart":
                convert_decimal(items),
                "count":
                len(items)
            })

        # ============================================
        # ➕ ADD TO CART
        # ============================================
        elif method == "POST":
            body = json.loads(
                event.get("body", "{}")
            )

            product_id = body.get("productId")

            quantity = int(
                body.get("quantity", 1)
            )

            if not product_id:
                return response(400, {
                    "message":
                    "productId required"
                })

            # 🔍 Product Exists
            product = products_table.get_item(
                Key={
                    "productId": product_id
                }
            ).get("Item")

            if not product:
                return response(404, {
                    "message":
                    "Product not found"
                })

            # 🛑 Cart Limit
            current_cart = cart_table.scan(
                FilterExpression=
                "userId = :uid",
                ExpressionAttributeValues={
                    ":uid": user_id
                },
                Select="COUNT"
            )

            if current_cart.get("Count", 0) >= 10:
                return response(400, {
                    "message":
                    "Cart limit reached"
                })

            # 💰 Price
            price = product.get("price", 0)

            discount = product.get("discount", 0)

            selling_price = (
                price -
                (price * discount / 100)
            )

            # 💾 Save Cart
            cart_item = {
                "cartId":
                str(uuid.uuid4()),
                "userId":
                user_id,
                "productId":
                product_id,
                "quantity":
                quantity,
                "name":
                product.get("name"),
                "description":
                product.get("description"),
                "imageUrl":
                product.get("imageUrl"),
                "price":
                price,
                "discount":
                discount,
                "sellingPrice":
                selling_price,
                "rating":
                product.get("rating", 0),
                "stock":
                product.get("stock", 0),
                "createdAt":
                datetime.utcnow().isoformat()
            }

            cart_table.put_item(
                Item=cart_item
            )

            return response(201, {
                "message":
                "Added to cart",
                "cart":
                convert_decimal(cart_item)
            })

        # ============================================
        # 🗑️ REMOVE FROM CART
        # ============================================
        elif method == "DELETE":
            body = json.loads(
                event.get("body", "{}")
            )

            product_id = body.get("productId")

            if not product_id:
                return response(400, {
                    "message":
                    "productId required"
                })

            cart_table.delete_item(
                Key={
                    "userId":
                    user_id,
                    "productId":
                    product_id
                }
            )

            return response(200, {
                "message":
                "Removed from cart"
            })

        # ============================================
        # ❌ INVALID METHOD
        # ============================================

        return response(405, {
            "message":
            "Method not allowed"
        })
    except jwt.ExpiredSignatureError:
        return response(401, {
            "message":
            "Token expired"
        })
    except jwt.InvalidTokenError:
        return response(401, {
            "message":
            "Invalid token"
        })
    except Exception as e:
        print("Cart Error:", str(e))

        return response(500, {
            "error": str(e)
        })