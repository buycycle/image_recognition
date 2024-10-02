FROM public.ecr.aws/lambda/python:3.9
# Install dependencies
COPY lambda/requirements.txt .
RUN pip install -r requirements.txt -t /lambda
# Copy the Lambda function code
COPY lambda /lambda
# Set the working directory
WORKDIR /lambda
# Command to run the Lambda function
CMD ["index.lambda_handler"]

