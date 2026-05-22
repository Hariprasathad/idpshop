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

orders_table = dynamodb.Table(
    os.environ["ORDERS_TABLE"]
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
            "OPTIONS,GET,POST"
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
        # 📦 GET MY ORDERS
        # ============================================

        if method == "GET":
            result = orders_table.scan(
                FilterExpression=
                "userId = :uid",
                ExpressionAttributeValues={
                    ":uid": user_id
                }
            )

            orders = result.get("Items", [])

            # 📦 SORT
            orders.sort(
                key=lambda x:
                x.get("createdAt", ""),
                reverse=True
            )

            # 📦 CHECK REVIEW
            for order in orders:
                review_check = reviews_table.scan(
                    FilterExpression="orderId = :oid",
                    ExpressionAttributeValues={
                        ":oid": order.get("orderId")
                    }
                )

                order["reviewed"] = review_check.get("Count", 0) > 0

            return response(200, {
                "orders":
                convert_decimal(orders),
                "count":
                len(orders)
            })

        # ============================================
        # 📦 CREATE ORDER
        # ============================================
        elif method == "POST":
            body = json.loads(
                event.get("body", "{}")
            )

            items = body.get("items", [])

            shipping_address = \
            body.get("address", "")

            if not items:
                return response(400, {
                    "message":
                    "No items provided"
                })

            created_orders = []

            total_order_amount = 0

            # ============================================
            # 🔁 PROCESS ITEMS
            # ============================================

            for item in items:
                product_id = item.get("productId")

                quantity = int(
                    item.get("quantity", 1)
                )

                # 🔍 PRODUCT
                prod_data = products_table.get_item(
                    Key={
                        "productId":
                        product_id
                    }
                ).get("Item")

                if not prod_data:
                    continue

                # 🛑 STOCK CHECK
                if int(prod_data.get("stock", 0)) < quantity:
                    return response(400, {
                        "message":
                        f"Not enough stock for {prod_data.get('name')}"
                    })

                # 💰 DISCOUNTED PRICE CALCULATION
                original_price = int(prod_data.get("price", 0))
                discount = int(prod_data.get("discount", 0))
                
                if discount > 0:
                    price = int(original_price - (original_price * discount / 100))
                else:
                    price = original_price

                item_total = price * quantity

                total_order_amount += item_total

                # 📦 CREATE ORDER
                order_item = {
                    "orderId":
                    str(uuid.uuid4()),
                    "userId":
                    user_id,
                    "sellerId":
                    prod_data.get("sellerId"),
                    "productId":
                    product_id,
                    "productName":
                    prod_data.get("name"),
                    "imageUrl":
                    prod_data.get("imageUrl"),
                    "quantity":
                    quantity,
                    "price": price,
                    "originalPrice": original_price,
                    "discount": discount,
                    "totalAmount":
                    item_total,
                    "shippingAddress":
                    shipping_address,
                    "paymentMethod":
                    "Cash on Delivery",
                    "status":
                    "Processing",
                    "createdAt":
                    datetime.utcnow().isoformat()
                }

                # 💾 SAVE ORDER
                orders_table.put_item(
                    Item=order_item
                )

                created_orders.append(order_item)

                # 📉 ATOMIC STOCK UPDATE (Prevents Race Conditions)
                products_table.update_item(
                    Key={"productId": product_id},
                    UpdateExpression="SET stock = stock - :q",
                    ConditionExpression="stock >= :q",
                    ExpressionAttributeValues={":q": quantity}
                )

            # ============================================
            # ✅ SUCCESS
            # ============================================

            return response(201, {
                "message":
                "Orders placed successfully",
                "count":
                len(created_orders),
                "totalAmount":
                convert_decimal(total_order_amount)
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
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return response(400, {
            "message": "Product out of stock"
        })
    except Exception as e:
        print("Order Error:", str(e))

        return response(500, {
            "error": str(e)
        })