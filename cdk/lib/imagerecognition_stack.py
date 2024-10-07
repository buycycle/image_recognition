from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_s3_notifications as s3_notifications,
    aws_apigateway as apigateway,
    aws_secretsmanager as secretsmanager,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    RemovalPolicy
)
from constructs import Construct
class ImageRecognitionStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # Define the secret name
        secret_name = "buycycle/ml/imagerecognition/google_service_account"
        # Create an S3 bucket for image uploads
        bucket = s3.Bucket(self, "ImageRecognitionBucket",
                           removal_policy=RemovalPolicy.DESTROY,
                           auto_delete_objects=True)
        # Create an SNS topic for image processing results
        topic = sns.Topic(self, "ImageProcessingResultsTopic",
                          display_name="Image Processing Results")
        # Create a Lambda function
        lambda_function = _lambda.Function(self, "ImageRecognitionFunction",
                                           runtime=_lambda.Runtime.PYTHON_3_11,  # Use a more recent runtime
                                           handler="index.lambda_handler",
                                           timeout=Duration.seconds(30),  # Increase timeout to 30 seconds
                                           code=_lambda.Code.from_asset("lambda_function.zip"),
                                           environment={
                                               "BUCKET_NAME": bucket.bucket_name,
                                               "SECRET_NAME": secret_name,
                                               "SNS_TOPIC_ARN": topic.topic_arn,
                                           })
        # Grant the Lambda function read access to the S3 bucket
        bucket.grant_read(lambda_function)
        # Add S3 event notification to trigger the Lambda function on object creation
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                      s3_notifications.LambdaDestination(lambda_function))
        # Grant the Lambda function access to the secret
        secret = secretsmanager.Secret.from_secret_name_v2(self, 'GoogleApiSecret', secret_name)
        secret.grant_read(lambda_function)
        # Grant the Lambda function permission to publish to the SNS topic
        topic.grant_publish(lambda_function)
        http_endpoint = "https://your-java-app-endpoint.com/sns-listener"
        topic.add_subscription(sns_subscriptions.UrlSubscription(http_endpoint))
