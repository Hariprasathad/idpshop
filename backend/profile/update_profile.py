import json
import boto3
import jwt
import os

# ============================================
# 🔥 DynamoDB
# ============================================

dynamodb = boto3.resource("dynamodb")

users_table = dynamodb.Table(
    os.environ["USERS_TABLE"]
)

SECRET_KEY = os.environ["SECRET_KEY"]


# ============================================
# 📦 Response
# ============================================

def response(status, body):

    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,PUT"
        },
        "body": json.dumps(body)
    }


# ============================================
# 🚀 Lambda Handler
# ============================================

def lambda_handler(event, context):

    try:

        # ============================================
        # 🔐 JWT AUTH
        # ============================================

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


        # ============================================
        # 📦 BODY
        # ============================================

        body = json.loads(event.get("body", "{}"))


        # ============================================
        # 🛠️ UPDATE USER
        # ============================================

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
                "#state": "state"
            },

            ExpressionAttributeValues={

                ":phone": body.get("phone", ""),

                ":addressLine": body.get("addressLine", ""),

                ":city": body.get("city", ""),

                ":state": body.get("state", ""),

                ":pincode": body.get("pincode", "")
            }
        )


        # ============================================
        # ✅ SUCCESS
        # ============================================

        return response(200, {

            "message": "Profile updated successfully"

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

        print("Update Profile Error:", str(e))

        return response(500, {
            "error": str(e)
        })