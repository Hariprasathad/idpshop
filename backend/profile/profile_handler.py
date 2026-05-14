import json
import boto3
import jwt
import os
from decimal import Decimal

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

users_table = dynamodb.Table(
    os.environ["USERS_TABLE"]
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
        # 👤 GET PROFILE
        # ============================================

        if method == "GET":

            result = users_table.get_item(

                Key={
                    "userId": user_id
                }
            )


            user = result.get("Item")


            if not user:

                return response(404, {

                    "message":
                    "User not found"
                })


            # ❌ REMOVE PASSWORD
            user.pop("password", None)


            return response(200, {

                "profile":
                convert_decimal(user)
            })


        # ============================================
        # ✏️ UPDATE PROFILE
        # ============================================

        elif method == "PUT":

            body = json.loads(
                event.get("body", "{}")
            )


            users_table.update_item(

                Key={
                    "userId": user_id
                },

                UpdateExpression="""
                    SET
                    phone = :phone,
                    addressLine = :addressLine,
                    city = :city,
                    #state = :state,
                    pincode = :pincode
                """,

                ExpressionAttributeNames={

                    "#state":
                    "state"
                },

                ExpressionAttributeValues={

                    ":phone":
                    body.get("phone", ""),

                    ":addressLine":
                    body.get("addressLine", ""),

                    ":city":
                    body.get("city", ""),

                    ":state":
                    body.get("state", ""),

                    ":pincode":
                    body.get("pincode", "")
                }
            )


            return response(200, {

                "message":
                "Profile updated successfully"
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

        print("Profile Handler Error:", str(e))

        return response(500, {

            "error": str(e)
        })