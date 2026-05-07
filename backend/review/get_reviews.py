import json
import boto3
import os
from decimal import Decimal

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

reviews_table = dynamodb.Table(os.environ["REVIEWS_TABLE"])


# ============================================
# 🔁 Convert Decimal
# ============================================

def convert_decimal(obj):

    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]

    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}

    elif isinstance(obj, Decimal):
        return int(obj)

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

        # 📦 Query params
        params = event.get("queryStringParameters") or {}

        product_id = params.get("productId")

        if not product_id:

            return response(400, {
                "message": "productId required"
            })


        # 🔍 Scan Reviews
        result = reviews_table.scan(
            FilterExpression="productId = :pid",
            ExpressionAttributeValues={
                ":pid": product_id
            }
        )

        reviews = result.get("Items", [])


        # ⭐ Average Rating
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

            "reviews": convert_decimal(reviews),

            "totalReviews": len(reviews),

            "averageRating": avg_rating

        })


    except Exception as e:

        print("Get Reviews Error:", str(e))

        return response(500, {
            "error": str(e)
        })