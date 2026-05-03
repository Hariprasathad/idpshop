import json
import boto3
import jwt
from boto3.dynamodb.conditions import Attr

# 🔧 DynamoDB setup
dynamodb = boto3.resource('dynamodb')
products_table = dynamodb.Table('hariprasath-products')
orders_table = dynamodb.Table('hariprasath-orders')

# 🔐 MUST match your login Lambda secret
SECRET_KEY = "your_secret"


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
        # 🔐 Get token
        token = event['headers'].get('Authorization')
        if not token:
            return response(401, {"message": "Unauthorized"})

        token = token.replace("Bearer ", "")

        # 🔐 Validate token
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return response(401, {"message": "Token expired"})
        except jwt.InvalidTokenError:
            return response(401, {"message": "Invalid token"})

        seller_email = decoded['email']

        # 📦 PRODUCTS TABLE
        products_res = products_table.scan(
            FilterExpression=Attr('sellerEmail').eq(seller_email)
        )
        products = products_res.get('Items', [])

        total_products = len(products)

        # ⚠️ Low stock (<5)
        low_stock = len([
            p for p in products if p.get('stock', 0) < 5
        ])

        # 🧾 ORDERS TABLE
        orders_res = orders_table.scan(
            FilterExpression=Attr('sellerEmail').eq(seller_email)
        )
        orders = orders_res.get('Items', [])

        total_orders = len(orders)

        # 💰 Total Sales = price × quantity
        total_sales = sum(
            o.get('price', 0) * o.get('quantity', 0)
            for o in orders
        )

        # ✅ Final response
        return response(200, {
            "totalProducts": total_products,
            "totalOrders": total_orders,
            "totalSales": total_sales,
            "lowStock": low_stock
        })

    except Exception as e:
        return response(500, {"error": str(e)})