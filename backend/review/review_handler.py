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

reviews_table = dynamodb.Table(
    os.environ["REVIEWS_TABLE"]
)

products_table = dynamodb.Table(
    os.environ["PRODUCTS_TABLE"]
)

SECRET_KEY = os.environ["SECRET_KEY"]

# ============================================
# 🔁 Convert Decimal
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
        return int(obj)

    if isinstance(obj, str) and 'd3r1l4tg7odjwk.cloudfront.net' in obj:
        return obj.replace('d3r1l4tg7odjwk.cloudfront.net', 'd3ox0o8h7so841.cloudfront.net')
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
            "OPTIONS,GET,POST"
        },
        "body": json.dumps(body)
    }

# ============================================
# 🔐 JWT AUTH
# ============================================

def get_user(event):
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

    return {
        "userId":
        decoded.get("userId"),
        "name":
        decoded.get("name", "User")
    }

# ============================================
# 🚀 Lambda Handler
# ============================================

def lambda_handler(event, context):
    try:
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
        # ⭐ GET REVIEWS
        # ============================================

        if method == "GET":
            params = event.get(
                "queryStringParameters"
            ) or {}

            product_id = params.get(
                "productId"
            )

            if not product_id:
                return response(400, {
                    "message":
                    "productId required"
                })

            result = reviews_table.scan(
                FilterExpression=
                "productId = :pid",
                ExpressionAttributeValues={
                    ":pid":
                    product_id
                }
            )

            reviews = result.get("Items", [])

            # ⭐ AVG RATING
            avg_rating = 0

            if reviews:
                total = sum(
                    review.get("rating", 0)
                    for review in reviews
                )

                avg_rating = round(
                    total / len(reviews),
                    1
                )

            return response(200, {
                "reviews":
                convert_decimal(reviews),
                "totalReviews":
                len(reviews),
                "averageRating":
                avg_rating
            })

        # ============================================
        # ⭐ ADD REVIEW
        # ============================================
        elif method == "POST":
            user = get_user(event)

            if not user:
                return response(401, {
                    "message":
                    "Unauthorized"
                })

            body = json.loads(
                event.get("body", "{}")
            )

            product_id = body.get("productId")
            order_id = body.get("orderId")
            rating = body.get("rating")
            comment = body.get("comment", "").strip()

            # ❌ VALIDATION
            if not product_id or not order_id:
                return response(400, {
                    "message": "productId and orderId required"
                })

            if rating is None:
                return response(400, {
                    "message": "rating required"
                })

            rating = int(rating)
            if rating < 1 or rating > 5:
                return response(400, {
                    "message": "rating must be between 1 and 5"
                })

            # 🔍 PRODUCT EXISTS
            product = products_table.get_item(
                Key={"productId": product_id}
            ).get("Item")

            if not product:
                return response(404, {
                    "message": "Product not found"
                })

            # 🚫 DUPLICATE REVIEW FOR SAME ORDER
            existing = reviews_table.scan(
                FilterExpression="orderId = :oid",
                ExpressionAttributeValues={":oid": order_id}
            )

            if existing.get("Items"):
                return response(400, {
                    "message": "Review already added for this order"
                })

            # ⭐ CREATE REVIEW
            review_item = {
                "reviewId": str(uuid.uuid4()),
                "orderId": order_id,
                "productId": product_id,
                "userId": user["userId"],
                "userName": user["name"],
                "rating": rating,
                "comment": comment,
                "createdAt": datetime.utcnow().isoformat()
            }

            # 💾 SAVE
            reviews_table.put_item(Item=review_item)

            return response(201, {
                "message": "Review added successfully",
                "review": review_item
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
        print("Review Handler Error:", str(e))

        return response(500, {
            "error": str(e)
        })
