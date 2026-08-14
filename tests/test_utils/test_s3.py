from io import BytesIO
from unittest.mock import MagicMock, patch

import botocore.exceptions
import pytest

from app.core.settings import settings
from app.utils.s3 import delete_file, get_url, init_bucket, upload_file


@patch("app.utils.s3.s3")
def test_init_bucket_exists(mock_s3):
    mock_s3.head_bucket.return_value = {}
    init_bucket()
    mock_s3.head_bucket.assert_called_once_with(Bucket=settings.S3_BUCKET_NAME)
    mock_s3.create_bucket.assert_not_called()


@patch("app.utils.s3.s3")
def test_init_bucket_creates(mock_s3):
    error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
    mock_s3.head_bucket.side_effect = botocore.exceptions.ClientError(
        error_response, "HeadBucket"
    )

    init_bucket()

    mock_s3.head_bucket.assert_called_once_with(Bucket=settings.S3_BUCKET_NAME)
    mock_s3.create_bucket.assert_called_once_with(Bucket=settings.S3_BUCKET_NAME)


@patch("app.utils.s3.s3")
def test_upload_file(mock_s3):
    fake_file = BytesIO(b"content")
    key = upload_file(fake_file, "test.txt", "path")

    assert key == "path/test.txt"
    mock_s3.upload_fileobj.assert_called_once_with(
        fake_file, settings.S3_BUCKET_NAME, "path/test.txt"
    )


@patch("app.utils.s3.s3")
def test_get_url(mock_s3):
    mock_s3.generate_presigned_url.return_value = "http://minio:9000/some/path"

    settings.DEBUG_MODE = True
    url = get_url("path/test.txt")

    mock_s3.generate_presigned_url.assert_called_once()
    assert url == settings.S3_EXTERNAL_URL + "/some/path"


@patch("app.utils.s3.s3")
def test_delete_file(mock_s3):
    mock_s3.delete_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 204}}

    res = delete_file("path/test.txt")

    assert res["ResponseMetadata"]["HTTPStatusCode"] == 204
    mock_s3.delete_object.assert_called_once_with(
        Bucket=settings.S3_BUCKET_NAME, Key="path/test.txt"
    )
