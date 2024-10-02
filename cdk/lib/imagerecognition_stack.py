
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_s3_notifications as s3_notifications,
    aws_apigateway as apigateway,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy
)
from constructs import Construct
class ImageRecognitionStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # Define the secret name
        secret_name = "buycycle/ml/imagerecognition"
        # Create an S3 bucket for image uploads
        bucket = s3.Bucket(self, "ImageRecognitionBucket",
                           removal_policy=RemovalPolicy.DESTROY,
                           auto_delete_objects=True)
        # Create a Lambda layer
        layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "MyLayer", "arn:aws:lambda:eu-central-1:930985312118:layer:my-layer"
        )
        # Create a Lambda function
        lambda_function = _lambda.Function(self, "ImageRecognitionFunction",
                                           runtime=_lambda.Runtime.PYTHON_3_11,  # Use a more recent runtime
                                           handler="index.lambda_handler",
                                           code=_lambda.Code.from_asset("lambda"),
                                           environment={
                                               "BUCKET_NAME": bucket.bucket_name,
                                               "SECRET_NAME": secret_name,
                                           },
                                           layers=[layer])
        # Grant the Lambda function read access to the S3 bucket
        bucket.grant_read(lambda_function)
        # Add S3 event notification to trigger the Lambda function
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                      s3_notifications.LambdaDestination(lambda_function))
        # Grant the Lambda function access to the secret
        secret = secretsmanager.Secret.from_secret_name_v2(self, 'GoogleApiSecret', secret_name)
        secret.grant_read(lambda_function)
        # Create an API Gateway REST API
        api = apigateway.RestApi(self, "ImageRecognitionApi",
                                 rest_api_name="Image Recognition Service",
                                 description="This service recognizes images.")
        # Create a resource and method for image uploads
        upload_resource = api.root.add_resource("upload")
        upload_integration = apigateway.LambdaIntegration(lambda_function)
        upload_resource.add_method("POST", upload_integration)

