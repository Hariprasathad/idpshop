import json
import boto3
import os
from decimal import Decimal

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

products_table = dynamodb.Table(
    os.environ["PRODUCTS_TABLE"]
)

reviews_table = dynamodb.Table(
    os.environ["REVIEWS_TABLE"]
)


# ============================================
# 🔁 Convert Decimal → int
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
            "Access-Control-Allow-Headers": "Content-Type",
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
        # 📦 Query Params
        # ============================================

        params = event.get("queryStringParameters") or {}

        query = params.get("q", "").strip().lower()

        if not query:

            return response(400, {
                "message": "Search query required"
            })


        # ============================================
        # 📦 Scan Products
        # ============================================

        result = products_table.scan()

        items = result.get("Items", [])


        # ============================================
        # 🔍 Filter Products
        # ============================================

        products = []

        for item in items:

            name = item.get("name", "").lower()

            description = item.get(
                "description",
                ""
            ).lower()


            # 🔍 Match
            if (
                query not in name and
                query not in description
            ):
                continue


            # ❌ Hide out of stock
            if item.get("stock", 0) <= 0:
                continue


            # ============================================
            # ⭐ Rating
            # ============================================

            review_result = reviews_table.scan(
                FilterExpression="productId = :pid",
                ExpressionAttributeValues={
                    ":pid": item.get("productId")
                }
            )

            reviews = review_result.get("Items", [])

            avg_rating = 0

            if reviews:

                total_rating = sum(
                    review.get("rating", 0)
                    for review in reviews
                )

                avg_rating = round(
                    total_rating / len(reviews),
                    1
                )


            # ============================================
            # 💰 Price
            # ============================================

            price = item.get("price", 0)

            discount = item.get("discount", 0)

            selling_price = price - (
                (price * discount) / 100
            )


            # ============================================
            # 📦 Response Product
            # ============================================

            products.append({

                "productId": item.get("productId"),

                "name": item.get("name"),

                "description": item.get("description", ""),

                "imageUrl": item.get("imageUrl", ""),

                "price": price,

                "discount": discount,

                "sellingPrice": int(selling_price),

                "rating": avg_rating,

                "stock": item.get("stock", 0),

                "total": item.get("total", 0),

                "sellerId": item.get("sellerId"),

                "createdAt": item.get("createdAt")
            })


        # ============================================
        # ✅ Success
        # ============================================

        return response(200, {

            "products": convert_decimal(products),

            "count": len(products)

        })


    except Exception as e:

        print("Search Products Error:", str(e))

        return response(500, {
            "error": str(e)
        })