from io import BytesIO

import boto3

from app.core.settings import settings

s3 = boto3.client("s3")


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
    return url
