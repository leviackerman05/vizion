import shutil
from pathlib import Path

from vizion.settings import settings


class Storage:
    @property
    def remote(self):
        return bool(settings.s3_bucket and settings.s3_endpoint_url)

    def client(self):
        import boto3
        from botocore.config import Config

        return boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3},
                connect_timeout=10,
                read_timeout=60,
                s3={"addressing_style": settings.s3_addressing_style},
            ),
        )

    def local_path(self, key):
        root = (settings.data_dir / "assets").resolve()
        path = (root / key).resolve()
        if root not in path.parents:
            raise ValueError("Invalid asset path")
        return path

    def upload(self, path: Path, key: str, content_type: str):
        if self.remote:
            self.client().upload_file(
                str(path),
                settings.s3_bucket,
                key,
                ExtraArgs={"ContentType": content_type, "CacheControl": "private, max-age=300"},
            )
        else:
            destination = self.local_path(key)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)

    def signed_url(self, key, download_name=None, content_type=None):
        params = {"Bucket": settings.s3_bucket, "Key": key}
        if download_name:
            params["ResponseContentDisposition"] = f'attachment; filename="{download_name}"'
        if content_type:
            params["ResponseContentType"] = content_type
        return self.client().generate_presigned_url("get_object", Params=params, ExpiresIn=3600)


storage = Storage()
