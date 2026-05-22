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

reviews_table = dynamodb.Table(
    os.environ["REVIEWS_TABLE"]
)

SECRET_KEY = os.environ["SECRET_KEY"]

# ============================================
# 🔁 Decimal Convert
# ============================================

def convert_decimal(obj):
    if isinstance(obj, list):
        return [
            convert_decimal(i)
            for i in obj
        ]
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
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://d3r1l4tg7odjwk.cloudfront.net",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
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
                "message":
                "Unauthorized"
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
        # ❤️ GET WISHLIST
        # ============================================

        if method == "GET":
            result = wishlist_table.scan(
                FilterExpression=
                "userId = :uid",
                ExpressionAttributeValues={
                    ":uid":
                    user_id
                }
            )

            wishlist_items = result.get(
                "Items",
                []
            )

            products = []

            # 📦 GET PRODUCT DATA
            for item in wishlist_items:
                product_result = products_table.get_item(
                    Key={
                        "productId":
                        item["productId"]
                    }
                )

                product = product_result.get(
                    "Item"
                )

                if product:
                    product["wishlistId"] = item["wishlistId"]
                    
                    # ⭐ Dynamic Rating & Pricing Calculation
                    reviews_result = reviews_table.scan(
                        FilterExpression="productId = :pid",
                        ExpressionAttributeValues={":pid": item["productId"]}
                    )
                    reviews = reviews_result.get("Items", [])
                    average_rating = 0
                    if reviews:
                        total = sum(review.get("rating", 0) for review in reviews)
                        average_rating = round(total / len(reviews), 1)
                    
                    product["rating"] = average_rating

                    # 💸 Calculate Selling Price
                    price = int(product.get("price", 0))
                    discount = int(product.get("discount", 0))
                    if discount > 0:
                        product["sellingPrice"] = int(price - (price * discount / 100))
                    else:
                        product["sellingPrice"] = price

                    products.append(product)

            return response(200, {
                "products":
                convert_decimal(products),
                "count":
                len(products)
            })

        # ============================================
        # ❤️ ADD WISHLIST
        # ============================================
        elif method == "POST":
            body = json.loads(
                event.get("body", "{}")
            )

            product_id = body.get(
                "productId"
            )

            if not product_id:
                return response(400, {
                    "message":
                    "productId required"
                })

            # 🔍 CHECK DUPLICATE
            existing = wishlist_table.scan(
                FilterExpression=
                "userId = :uid AND productId = :pid",
                ExpressionAttributeValues={
                    ":uid":
                    user_id,
                    ":pid":
                    product_id
                }
            )

            # ❤️ REMOVE IF EXISTS
            if existing.get("Items"):
                existing_item = existing[
                    "Items"
                ][0]

                wishlist_table.delete_item(
                    Key={
                        "wishlistId":
                        existing_item["wishlistId"]
                    }
                )

                return response(200, {
                    "message":
                    "Removed from wishlist",
                    "wishlisted":
                    False
                })

            # ❤️ ADD NEW
            wishlist_item = {
                "wishlistId":
                str(uuid.uuid4()),
                "userId":
                user_id,
                "productId":
                product_id,
                "createdAt":
                datetime.utcnow().isoformat()
            }

            wishlist_table.put_item(
                Item=wishlist_item
            )

            return response(201, {
                "message":
                "Added to wishlist",
                "wishlisted":
                True
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
        print("Wishlist Handler Error:", str(e))

        return response(500, {
            "error":
            str(e)
        })