from io import BytesIO

import boto3
import botocore

from app.core.settings import settings

if settings.DEBUG_MODE:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url="http://minio:9000",
    )
else:
    s3 = boto3.client("s3")


def init_bucket():
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except botocore.exceptions.ClientError:
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)


def upload_file(file: BytesIO, filename: str, path: str):
    key = f"{path}/{filename}"
    s3.upload_fileobj(file, settings.S3_BUCKET_NAME, key)
    return key


def get_url(key: str):
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=3600,
    )
    if settings.DEBUG_MODE:
        url = url.replace("http://minio:9000", settings.S3_EXTERNAL_URL)
    return url


def delete_file(key: str):
    response = s3.delete_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
    )
    return response
