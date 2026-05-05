import json
import boto3
import os
import uuid

s3 = boto3.client('s3')
BUCKET = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    try:
        file_name = f"{uuid.uuid4()}.jpg"

        upload_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET,
                'Key': file_name,
                'ContentType': '*/*'   # ⭐ IMPORTANT FIX
            },
            ExpiresIn=300
        )

        image_url = f"https://{BUCKET}.s3.amazonaws.com/{file_name}"

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "uploadUrl": upload_url,
                "imageUrl": image_url
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }