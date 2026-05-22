import json
import boto3
import jwt
import os
from boto3.dynamodb.conditions import Attr


dynamodb = boto3.resource('dynamodb')

products_table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])

SECRET_KEY = os.environ['SECRET_KEY']


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


def lambda_handler(event, context):
    try:
        # ============================================
        # 🌐 METHOD (Robust Extraction)
        # ============================================
        method = event.get("httpMethod")
        if not method:
            method = event.get("requestContext", {}).get("http", {}).get("method")

        # 🛡️ OPTIONS PREFLIGHT
        if method == "OPTIONS":
            return response(200, {"message": "CORS Preflight OK"})

        # 🔐 Auth
        headers = event.get('headers', {})
        token = headers.get('Authorization') or headers.get('authorization')

        if not token:
            return response(401, {"message": "Unauthorized"})

        token = token.replace("Bearer ", "")
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        seller_id = decoded.get('userId')

        # 📦 Fetch products
        products_res = products_table.scan(
            FilterExpression=Attr('sellerId').eq(seller_id)
        )
        products = products_res.get('Items', [])

        total_products = len(products)

        # 🟡 Low stock (<5)
        low_stock = len([p for p in products if int(p.get("stock", 0)) <= 5])

        # 📦 Fetch orders
        orders_res = orders_table.scan()
        orders = orders_res.get('Items', [])

        # Filter seller orders (simple version)
        seller_orders = [o for o in orders if o.get("sellerId") == seller_id]

        total_orders = len(seller_orders)

        # 💰 Total sales
        total_sales = sum(float(o.get("totalAmount", 0)) for o in seller_orders)

        return response(200, {
            "totalProducts": total_products,
            "totalOrders": total_orders,
            "totalSales": total_sales,
            "lowStock": low_stock
        })

    except Exception as e:
        print(f"Seller Stats Error: {str(e)}") # ⭐ Log to CloudWatch
        return response(500, {"error": str(e)})