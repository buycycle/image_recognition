# buycycle Image Recognition Model
Welcome to the buycycle Image Recognition Model project! This repository contains the code and resources for a serverless image recognition model designed to recognize and classify images of bicycles. The project leverages AWS Lambda and Google Vision AI API to detect web entities and filter results based on a certain score threshold. The ultimate goal is to match user-uploaded bicycle images to a predefined set of family IDs using a word matching algorithm.
## Project Overview
### Objective
The primary objective of this project is to develop a robust image recognition model that can accurately identify and classify bicycle images uploaded by users. The model will utilize Google Vision AI's Web Detection feature to extract relevant web entities and match them to a predefined set of family IDs.
### Key Features
1. **Image Upload**: Users can upload images of bicycles to an S3 bucket.
2. **AWS Lambda Integration**: An S3 event triggers a Lambda function to process the uploaded image.
3. **Google Vision AI Integration**: The Lambda function sends the image to Google Vision AI for web entity detection.
4. **Score Filtering**: The detected web entities are filtered based on a predefined score threshold to ensure accuracy.
5. **Word Matching Algorithm**: A custom word matching algorithm is used to match the filtered web entities to a predefined set of family IDs.
6. **Result Return**: The top n similar matches are returned directly from the Lambda function.
### Schematic
[View Schematic](https://excalidraw.com/#json=_mKcmwEdqvZDs1Urlapc7,crsQy1z9jc7mZNr8755P3g)
## Getting Started
### Prerequisites
- An AWS account with access to S3 and Lambda.
- A Google Cloud account with access to the Vision AI API.
- AWS CLI and CDK installed on your local machine.
- Python 3.7 or higher.
### Installation
1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/bicycle-image-recognition-lambda.git
   cd bicycle-image-recognition-lambda
   ```
2. **Deploy the CDK Stack**
     ```bash
     cdk deploy
     ```
## Usage
1. **Upload an Image**
   - Use a tool like Postman or curl to upload an image to the API Gateway endpoint.
     ```bash
     curl -X POST -F "file=@path/to/your/image.jpg" https://<api-id>.execute-api.<region>.amazonaws.com/prod/upload
     ```
2. **Trigger Lambda Function**
   - The API Gateway will trigger the Lambda function, which will process the image and return the most likely `family_id`.
3. **View Results**
   - The response from the Lambda function will be returned directly to the client.
## How It Works
### AWS Lambda Integration
The Lambda function is triggered by an S3 event whenever a new image is uploaded to the designated S3 bucket. The function reads the image from S3 and sends it to Google Vision AI's Web Detection API.
### Google Vision AI Integration
The Lambda function sends the uploaded image to Google Vision AI's Web Detection API. The API returns a list of web entities, full matching images, partial matching images, pages with matching images, visually similar images, and best guess labels.
### Score Filtering
The returned web entities are filtered based on a predefined score threshold to ensure that only the most relevant entities are considered.
### Word Matching Algorithm
A custom word matching algorithm is used to match the filtered web entities to a predefined set of family IDs. The algorithm calculates the similarity between the web entity descriptions and the family IDs to determine the most likely match.
### Result Return
The most likely match is returned directly from the Lambda function.
## Contributing
We welcome contributions to this project! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.
## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
## Acknowledgments
- [Google Cloud Vision API](https://cloud.google.com/vision) for providing the web detection capabilities.
- [AWS Lambda](https://aws.amazon.com/lambda/) for serverless computing.
- [AWS S3](https://aws.amazon.com/s3/) for storage.

