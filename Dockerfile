FROM public.ecr.aws/lambda/python:3.9
# Set the working directory
# Install dependencies
COPY /cdk/lambda/requirements.txt .
RUN pip install -r requirements.txt -t /cdk/lambda
# Copy the Lambda function code
COPY cdk/lambda /lambda
# Set the working directory
WORKDIR /lambda
# Command to run the Lambda function
CMD ["index.lambda_handler"]

