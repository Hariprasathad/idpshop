import json
import boto3
import jwt
import os
from boto3.dynamodb.conditions import Attr
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
            "OPTIONS,GET,PUT"
        },
        "body": json.dumps(body)
    }

# ============================================
# 🔐 JWT AUTH
# ============================================

def get_seller_id(event):
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

        seller_id = get_seller_id(event)

        if not seller_id:
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
        # 📦 GET SELLER ORDERS
        # ============================================

        if method == "GET":
            result = orders_table.scan(
                FilterExpression=
                Attr("sellerId").eq(seller_id)
            )

            orders = convert_decimal(
                result.get("Items", [])
            )

            # 📦 SORT LATEST FIRST
            orders.sort(
                key=lambda x:
                x.get("createdAt", ""),
                reverse=True
            )

            return response(200, {
                "orders":
                orders
            })

        # ============================================
        # 🔄 UPDATE ORDER STATUS
        # ============================================
        elif method == "PUT":
            body = json.loads(
                event.get("body", "{}")
            )

            order_id = body.get("orderId")

            new_status = body.get("status")

            if not order_id or not new_status:
                return response(400, {
                    "message":
                    "orderId and status required"
                })

            # 🔒 ALLOWED STATUS
            allowed_status = [
                "Processing",
                "Shipped",
                "Delivered"
            ]

            if new_status not in allowed_status:
                return response(400, {
                    "message":
                    "Invalid status value"
                })

            # 🔍 CHECK ORDER
            item = orders_table.get_item(
                Key={
                    "orderId":
                    order_id
                }
            ).get("Item")

            if not item:
                return response(404, {
                    "message":
                    "Order not found"
                })

            # 🔒 CHECK OWNERSHIP
            if item.get("sellerId") != seller_id:
                return response(403, {
                    "message":
                    "Forbidden"
                })

            # 🔄 UPDATE STATUS
            orders_table.update_item(
                Key={
                    "orderId":
                    order_id
                },
                UpdateExpression=
                "SET #s = :status",
                ExpressionAttributeNames={
                    "#s":
                    "status"
                },
                ExpressionAttributeValues={
                    ":status":
                    new_status
                }
            )

            return response(200, {
                "message":
                "Order status updated successfully"
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
        print("Seller Order Handler Error:", str(e))

        return response(500, {
            "error":
            str(e)
        })
