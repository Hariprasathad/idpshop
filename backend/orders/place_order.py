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
        
        items = body.get("items", [])
        shipping_address = body.get("address", "")

        if not items:
            return response(400, {"message": "No items provided"})

        created_orders = []
        total_order_amount = 0

        # Process each item
        for item in items:
            product_id = item.get("productId")
            quantity = int(item.get("quantity", 1))

            # 🔍 Product Exists & Stock Check
            prod_data = products_table.get_item(Key={"productId": product_id}).get("Item")
            if not prod_data:
                continue # Skip or handle error

            if int(prod_data.get("stock", 0)) < quantity:
                return response(400, {"message": f"Not enough stock for {prod_data.get('name')}"})

            # 💰 Calculation
            price = int(prod_data.get("sellingPrice") or prod_data.get("price"))
            item_total = price * quantity
            total_order_amount += item_total

            # 💾 Create Order
            order_id = str(uuid.uuid4())
            order_item = {
                "orderId": order_id,
                "userId": user_id,
                "sellerId": prod_data.get("sellerId"),
                "productId": product_id,
                "productName": prod_data.get("name"),
                "imageUrl": prod_data.get("imageUrl"),
                "quantity": quantity,
                "price": price,
                "totalAmount": item_total,
                "shippingAddress": shipping_address,
                "paymentMethod": "Cash on Delivery",
                "status": "Processing",
                "createdAt": datetime.utcnow().isoformat()
            }

            orders_table.put_item(Item=order_item)
            created_orders.append(order_item)

            # 📉 Update Stock
            products_table.update_item(
                Key={"productId": product_id},
                UpdateExpression="SET stock = stock - :q",
                ExpressionAttributeValues={":q": quantity}
            )

        return response(201, {
            "message": "Orders placed successfully",
            "count": len(created_orders),
            "totalAmount": convert_decimal(total_order_amount)
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

        print("Place Order Error:", str(e))

        return response(500, {
            "error": str(e)
        })
