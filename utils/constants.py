HttpResponseMsg = dict(
    SUCCESS='Success',
    FAILED='Failed'
)

HttpStatusCode = dict(
    SUCCESS=200,
    SUCCESS_CREATE=201,
    CLIENT_ERROR=400,
    SERVER_ERROR=500,
    AUTH_ERROR=401
)

HttpErrorMsg = dict(
    CLIENT_ERROR='Bad Request',
    SERVER_ERROR='Internal Server Error',
    AUTH_ERROR='Unauthorised'
)

INITIATED = 'initiated'
PROCESSING = 'Running'
DONE = 'Complete'
FAILED = 'Failed'

DEFAULT_TIMEZONE = 'America/Chicago'
AWS_REGION = 'ap-south-1'
BUCKET_NAME = 'store-monitor-reports'
S3_URL = f'http:///{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/'
