import json
import boto3
import uuid
import time
import random
import logging

from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
TOKEN_EXPIRATION_SECONDS = 900  # 15 minutes
GENERIC_ERROR_MESSAGE = 'The auth token and verification code pair is invalid or has expired - please request a new auth token'
INTERNAL_ERROR_MESSAGE = 'An internal error occurred - contact support@swebench.com with event id verify-auth-token/{log_id}'

def create_response(status_code: int, body: dict) -> dict:
    return {
        'statusCode': status_code,
        'body': json.dumps(body)
    }

def get_auth_tokens_by_email(email: str, table) -> list:
    logger.info(f"Getting auth tokens for email: {email}")
    items = table.query(
        IndexName='email-created-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={
            ':email': email
        }
    )
    return items['Items']

def deverify_existing_tokens(email: str, table) -> None:
    logger.info(f"Deverifying existing tokens for email: {email}")
    current_time = int(time.time())
    all_auth_tokens = get_auth_tokens_by_email(email, table)
    with table.batch_writer() as batch:
        for item in all_auth_tokens:
            if item['verified']:
                logger.info(f"Deverifying token: {item['token']}")
                item['verified'] = False
                item['last_used'] = current_time
                batch.put_item(Item=item)

def lambda_handler(event: dict, context) -> dict:
    logger.info("Starting auth token verification handler")
    # return a standard error response for most errors (don't leak any information about which auth tokens exist or not)
    generic_error = create_response(400, {'error': GENERIC_ERROR_MESSAGE})
    
    try:
        event_body = json.loads(event['body'])
        auth_token = event_body['auth_token']
        verification_code = event_body['verification_code']
        
        if not isinstance(auth_token, str) or not isinstance(verification_code, str):
            logger.warning("Invalid input types received")
            return create_response(400, {'error': 'Invalid input types'})
        if not auth_token.strip() or not verification_code.strip():
            logger.warning("Empty inputs received")
            return create_response(400, {'error': 'Empty inputs not allowed'})
            
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('requested_auth_tokens')
        try:
            logger.info(f"Retrieving auth token: {auth_token}")
            response = table.get_item(Key={'token': auth_token})
            if 'Item' not in response:
                logger.warning(f"Auth token not found: {auth_token}")
                return generic_error
            item = response['Item']
            current_time = int(time.time())
            
            # Check if token was created within expiration time
            if current_time - item['created'] > TOKEN_EXPIRATION_SECONDS:
                logger.warning(f"Token expired: {auth_token}, {current_time} - {item['created']} > {TOKEN_EXPIRATION_SECONDS}")
                return generic_error
            if item['verification_code'] != verification_code:
                logger.warning(f"Invalid verification code for token: {auth_token} - {verification_code} vs {item['verification_code']}")
                return generic_error
            email = item['email']
            deverify_existing_tokens(email, table)
            item['verified'] = True
            item['last_used'] = current_time
            logger.info(f"Verifying token for email: {email}")
            table.put_item(Item=item)
            logger.info("Auth token verification completed successfully")
            return create_response(200, {'message': 'Auth token verified successfully'})
        except ClientError as e:
            logger.error(f"DynamoDB error: {e}")
            log_id = context.aws_request_id
            return create_response(500, {'error': INTERNAL_ERROR_MESSAGE.format(log_id=log_id)})
    except Exception as e:
        logger.error(f"Error parsing event body: {e}")
        return create_response(400, {'error': f'Error parsing event body: {e}'})
