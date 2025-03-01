import json
from youtube_summarizer import YouTubeSummarizer

def lambda_handler(event, context):
    """
    AWS Lambda function handler that processes a YouTube video ID and returns a summarized JSON response.
    
    Parameters:
    - event: Contains incoming data, expected to have a 'video_id' parameter
    - context: AWS Lambda context
    
    Returns:
    - A JSON response with the video summary or an error message
    """
    try:
        # Extract video_id from the event
        if 'video_id' in event:
            video_id = event['video_id']
        elif 'queryStringParameters' in event and event['queryStringParameters'] and 'video_id' in event['queryStringParameters']:
            # Handle API Gateway requests
            video_id = event['queryStringParameters']['video_id']
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing video_id parameter'})
            }
        
        # Initialize the summarizer and get the JSON summary
        summarizer = YouTubeSummarizer(video_id)
        summary_json = summarizer.jsonSummary()
        
        # Return the summary as the Lambda response
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': summary_json
        }
    
    except Exception as e:
        # Handle errors
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process the video summary'
            })
        }