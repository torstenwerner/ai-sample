# YouTube Summarizer Lambda Deployment Guide

This guide explains how to deploy the YouTube Summarizer as an AWS Lambda function.

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- Python 3.9+ installed locally

## Deployment Steps

### 1. Prepare the Lambda Package

1. Create a deployment directory and copy the required files:

```bash
mkdir deployment
cp lambda_function.py youtube_summarizer.py requirements.txt deployment/
cd deployment
```

2. Install dependencies in the deployment directory:

```bash
pip install -r requirements.txt -t .
```

3. Create a ZIP file for deployment:

```bash
zip -r ../youtube_summarizer_lambda.zip .
```

### 2. Create Lambda Function in AWS

1. Create the Lambda function using AWS CLI:

```bash
aws lambda create-function \
    --function-name YouTubeSummarizerFunction \
    --runtime python3.9 \
    --role arn:aws:iam::<YOUR-ACCOUNT-ID>:role/lambda-basic-execution \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://../youtube_summarizer_lambda.zip \
    --timeout 60 \
    --memory-size 256
```

2. Or create it via the AWS Console:
   - Navigate to Lambda in the AWS Console
   - Click "Create function"
   - Choose "Author from scratch"
   - Set function name to "YouTubeSummarizerFunction"
   - Select Python 3.9 runtime
   - Choose an existing role or create a new one with basic Lambda permissions
   - Click "Create function"
   - Upload the ZIP file in the "Code" tab

### 3. Configure Environment Variables

Set the required environment variables:

```bash
aws lambda update-function-configuration \
    --function-name YouTubeSummarizerFunction \
    --environment "Variables={OPENAI_API_KEY=your-api-key-here}"
```

Or configure via the AWS Console:
- Go to the Lambda function
- Navigate to the "Configuration" tab
- Click on "Environment variables"
- Add the OPENAI_API_KEY variable

### 4. Set Up API Gateway (Optional)

To create a REST API endpoint for the Lambda function:

1. Create a new API Gateway
2. Create a new resource and method (GET)
3. Configure the integration with your Lambda function
4. Add a query parameter for video_id
5. Deploy the API

### 5. Test the Function

Test the Lambda function using the AWS CLI:

```bash
aws lambda invoke \
    --function-name YouTubeSummarizerFunction \
    --payload '{"video_id": "dMcZPkYUBxU"}' \
    response.json

cat response.json
```

Or test via the AWS Console using the test event feature.

## Troubleshooting

- **Dependencies**: Make sure all required dependencies are included in the deployment package
- **Permissions**: Ensure the Lambda role has appropriate permissions
- **Timeout**: If the function times out, increase the timeout limit in the configuration
- **Memory**: If you encounter memory issues, increase the allocated memory

## Security Considerations

- Store API keys in AWS Secrets Manager for production use
- Restrict API Gateway access as needed
- Consider adding API key authentication for the API endpoint