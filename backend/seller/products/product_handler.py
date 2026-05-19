import json
import boto3
import jwt
import uuid
import os
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

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

        return {

            k: convert_decimal(v)

            for k, v in obj.items()
        }


    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)

    elif isinstance(obj, str) and "hariprasath-product-images.s3" in obj:
        return obj.replace(
            "hariprasath-product-images.s3.ap-southeast-1.amazonaws.com", 
            "d3r1l4tg7odjwk.cloudfront.net/images"
        ).replace(
            "hariprasath-product-images.s3.amazonaws.com", 
            "d3r1l4tg7odjwk.cloudfront.net/images"
        )

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
            "OPTIONS,GET,POST,PUT,DELETE"
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
        # 📦 GET SELLER PRODUCTS
        # ============================================

        if method == "GET":

            params = event.get(
                "queryStringParameters"
            ) or {}


            limit = int(
                params.get("limit", 10)
            )

            last_key = params.get(
                "lastKey"
            )


            scan_kwargs = {

                "FilterExpression":
                Attr("sellerId").eq(seller_id),

                "Limit":
                limit
            }


            # 🔥 PAGINATION
            if last_key:

                scan_kwargs[
                    "ExclusiveStartKey"
                ] = json.loads(last_key)


            result = products_table.scan(
                **scan_kwargs
            )


            items = convert_decimal(

                result.get("Items", [])
            )


            return response(200, {

                "products":
                items,

                "lastKey":
                result.get("LastEvaluatedKey")
            })


        # ============================================
        # ➕ ADD PRODUCT
        # ============================================

        elif method == "POST":

            body = json.loads(
                event.get("body", "{}")
            )


            product = {

                "productId":
                str(uuid.uuid4()),

                "name":
                body.get("name"),

                "category":
                body.get("category", ""),

                "price":
                int(body.get("price") or 0),

                "discount":
                int(body.get("discount") or 0),

                "description":
                body.get("description"),

                "stock":
                int(body.get("stock") or 0),

                "total":
                int(body.get("total") or 0),

                "imageUrl":
                body.get("imageUrl", ""),

                "createdAt":
                datetime.utcnow().isoformat(),

                "sellerId":
                seller_id
            }


            products_table.put_item(
                Item=product
            )


            return response(200, {

                "message":
                "Product added successfully"
            })


        # ============================================
        # ✏️ UPDATE PRODUCT
        # ============================================

        elif method == "PUT":

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


            # 🔒 CHECK OWNER
            item = products_table.get_item(

                Key={
                    "productId":
                    product_id
                }

            ).get("Item")


            if not item:

                return response(404, {

                    "message":
                    "Product not found"
                })


            if item.get("sellerId") != seller_id:

                return response(403, {

                    "message":
                    "Forbidden"
                })


            # 🛠️ BUILD UPDATE
            update_expr = []

            expr_values = {}

            expr_names = {}


            fields = [

                "name",

                "category",

                "price",

                "discount",

                "description",

                "stock",

                "total",

                "imageUrl"
            ]


            for field in fields:

                if field in body:

                    key_name = f"#{field}"

                    value_name = f":{field}"


                    update_expr.append(

                        f"{key_name} = {value_name}"
                    )

                    expr_values[
                        value_name
                    ] = body[field]

                    expr_names[
                        key_name
                    ] = field


            if not update_expr:

                return response(400, {

                    "message":
                    "No fields to update"
                })


            # 🔥 UPDATE
            products_table.update_item(

                Key={
                    "productId":
                    product_id
                },

                UpdateExpression=
                "SET " + ", ".join(update_expr),

                ExpressionAttributeValues=
                expr_values,

                ExpressionAttributeNames=
                expr_names
            )


            return response(200, {

                "message":
                "Product updated successfully"
            })


        # ============================================
        # 🗑️ DELETE PRODUCT
        # ============================================

        elif method == "DELETE":

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


            # 🔒 CHECK OWNER
            item = products_table.get_item(

                Key={
                    "productId":
                    product_id
                }

            ).get("Item")


            if not item:

                return response(404, {

                    "message":
                    "Product not found"
                })


            if item.get("sellerId") != seller_id:

                return response(403, {

                    "message":
                    "Forbidden"
                })


            # 🗑️ DELETE
            products_table.delete_item(

                Key={
                    "productId":
                    product_id
                }
            )


            return response(200, {

                "message":
                "Product deleted successfully"
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

        print("Seller Product Handler Error:", str(e))

        return response(500, {

            "error":
            str(e)
        })