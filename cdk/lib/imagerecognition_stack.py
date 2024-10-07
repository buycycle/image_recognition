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
        # Create a Lambda function for uploading images to S3
        upload_lambda = _lambda.Function(self, "UploadFunction",
                                         runtime=_lambda.Runtime.PYTHON_3_11,
                                         handler="index.upload_handler",  # Specify the upload handler
                                         timeout=Duration.seconds(30),
                                         code=_lambda.Code.from_asset("lambda_function.zip"),
                                         environment={
                                             "BUCKET_NAME": bucket.bucket_name,
                                             "SNS_TOPIC_ARN": topic.topic_arn,
                                         })
        # Grant the upload Lambda function write access to the S3 bucket
        bucket.grant_put(upload_lambda)
        # Create a Lambda function for image recognition
        recognition_lambda = _lambda.Function(self, "ImageRecognitionFunction",
                                              runtime=_lambda.Runtime.PYTHON_3_11,
                                              handler="index.recognition_handler",  # Specify the recognition handler
                                              timeout=Duration.seconds(30),
                                              code=_lambda.Code.from_asset("lambda_function.zip"),
                                              environment={
                                                  "BUCKET_NAME": bucket.bucket_name,
                                                  "SECRET_NAME": secret_name,
                                                  "SNS_TOPIC_ARN": topic.topic_arn,
                                              })
        # Grant the recognition Lambda function read access to the S3 bucket
        bucket.grant_read(recognition_lambda)
        # Add S3 event notification to trigger the recognition Lambda function on object creation
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                      s3_notifications.LambdaDestination(recognition_lambda))
        # Grant the recognition Lambda function access to the secret
        secret = secretsmanager.Secret.from_secret_name_v2(self, 'GoogleApiSecret', secret_name)
        secret.grant_read(recognition_lambda)
        # Grant the recognition Lambda function permission to publish to the SNS topic
        topic.grant_publish(recognition_lambda)
        # Optionally, subscribe an email to the SNS topic
        topic.add_subscription(sns_subscriptions.EmailSubscription("sebastian@buycycle.com"))

