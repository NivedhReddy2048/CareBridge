from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class PrivateMediaStorage(S3Boto3Storage):
    location = 'private'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False
    
    def __init__(self, *args, **kwargs):
        self.querystring_auth = True
        self.querystring_expire = getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 300)
        super().__init__(*args, **kwargs)
