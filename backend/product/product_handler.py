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
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://d3r1l4tg7odjwk.cloudfront.net",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization"
        },
        "body": json.dumps(body)
    }


# ============================================
# ⭐ CALCULATE RATING
# ============================================

def get_average_rating(product_id):

    review_result = reviews_table.scan(

        FilterExpression=
        "productId = :pid",

        ExpressionAttributeValues={

            ":pid": product_id
        }
    )


    reviews = review_result.get("Items", [])


    if not reviews:

        return 0


    total_rating = sum(

        review.get("rating", 0)

        for review in reviews
    )


    return round(

        total_rating / len(reviews),

        1
    )


# ============================================
# 📦 FORMAT PRODUCT
# ============================================

def format_product(item):

    price = item.get("price", 0)

    discount = item.get("discount", 0)

    selling_price = price - (
        (price * discount) / 100
    )


    return {

        "productId":
        item.get("productId"),

        "name":
        item.get("name"),

        "description":
        item.get("description", ""),

        "imageUrl":
        item.get("imageUrl", ""),

        "price":
        price,

        "discount":
        discount,

        "sellingPrice":
        int(selling_price),

        "rating":
        get_average_rating(
            item.get("productId")
        ),

        "stock":
        item.get("stock", 0),

        "total":
        item.get("total", 0),

        "sellerId":
        item.get("sellerId"),

        "createdAt":
        item.get("createdAt")
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
        # 🛡️ OPTIONS PREFLIGHT
        # ============================================
        if method == "OPTIONS":
            return response(200, {"message": "CORS Preflight OK"})


        # ============================================
        # 📦 QUERY PARAMS
        # ============================================

        params = event.get("queryStringParameters") or {}


        # ============================================
        # 🔍 SEARCH PRODUCTS
        # ============================================

        query = params.get("q")


        if query:

            query = query.strip().lower()

            result = products_table.scan()

            items = result.get("Items", [])

            products = []


            for item in items:

                name = item.get(
                    "name",
                    ""
                ).lower()


                description = item.get(
                    "description",
                    ""
                ).lower()


                # 🔍 MATCH
                if (

                    query not in name

                    and

                    query not in description
                ):

                    continue


                # ❌ HIDE OUT OF STOCK
                if item.get("stock", 0) <= 0:

                    continue


                products.append(
                    format_product(item)
                )


            return response(200, {

                "products":
                convert_decimal(products),

                "count":
                len(products)
            })


        # ============================================
        # 📦 GET PRODUCTS
        # ============================================

        limit = int(
            params.get("limit", 10)
        )

        last_key = params.get("lastKey")


        scan_params = {

            "Limit": limit
        }


        # 🔥 PAGINATION
        if last_key:

            scan_params["ExclusiveStartKey"] = {

                "productId": last_key
            }


        result = products_table.scan(
            **scan_params
        )

        items = result.get("Items", [])


        products = []


        for item in items:

            # ❌ HIDE OUT OF STOCK
            if item.get("stock", 0) <= 0:

                continue


            products.append(
                format_product(item)
            )


        # 🔑 NEXT PAGE
        next_key = None


        if "LastEvaluatedKey" in result:

            next_key = result[
                "LastEvaluatedKey"
            ]["productId"]


        # ============================================
        # ✅ SUCCESS
        # ============================================

        return response(200, {

            "products":
            convert_decimal(products),

            "count":
            len(products),

            "lastKey":
            next_key
        })


    except Exception as e:

        print("Product Handler Error:", str(e))

        return response(500, {

            "error": str(e)
        })