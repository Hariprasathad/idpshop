import json
import boto3
import os
import uuid

from botocore.config import Config

s3 = boto3.client(
    's3',
    region_name='ap-southeast-1',
    config=Config(signature_version='s3v4')
)
BUCKET = os.environ['BUCKET_NAME']

def lambda_handler(event, context):
    try:
        params = event.get("queryStringParameters") or {}
        content_type = params.get("contentType", "image/jpeg")
        extension = content_type.split("/")[-1]
        file_name = f"{uuid.uuid4()}.{extension}"

        upload_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET,
                'Key': f"images/{file_name}",
                'ContentType': content_type
            },
            ExpiresIn=300
        )

        # Use CloudFront domain for images
        CLOUDFRONT_DOMAIN = "d3ox0o8h7so841.cloudfront.net" 
        image_url = f"https://{CLOUDFRONT_DOMAIN}/images/{file_name}"

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
