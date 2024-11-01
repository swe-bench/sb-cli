import json
import boto3
import uuid
import time
import smtplib
import random
import secrets
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


RETRY_TIME_SECONDS = 300
INTERNAL_ERROR_MESSAGE = 'An internal error occurred - contact support@swebench.com with event id gen-auth-token/{log_id}'


def create_response(status_code: int, body: dict) -> dict:
    return {
        'statusCode': status_code,
        'body': json.dumps(body)
    }


def get_fastmail_password():
    logger.info("Retrieving Fastmail password from Secrets Manager")
    secret_name = "swebm/smtp-fastmail-password"
    region_name = "us-east-2"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    secret = json.loads(get_secret_value_response['SecretString'])
    return secret["password"]


def send_message(to_addr, verification_code, subject):
    logger.info(f"Sending verification email to {to_addr}")
    username = "carlos@swerl.ai"
    from_addr = "evals@swebench.com"
    password = get_fastmail_password()
    smtp = smtplib.SMTP_SSL('smtp.fastmail.com', port=465)
    smtp.login(username, password)
    msg_root = MIMEMultipart()
    msg_root['Subject'] = subject
    msg_root['From'] = from_addr
    msg_root['To'] = to_addr
    msg_alternative = MIMEMultipart('alternative')
    msg_root.attach(msg_alternative)
    email_body = f"""
    Hello,

    Thank you for requesting access to SWE-bench. To verify your email address, please use the following verification code:

    {verification_code}

    This code will expire in 5 minutes. If you didn't request this code, please ignore this email.

    Best regards,
    SWE-bench Team
    """
    msg_alternative.attach(MIMEText(email_body))
    smtp.sendmail(from_addr, to_addr, msg_root.as_string())
    smtp.quit()
    logger.info("Email sent successfully")


def generate_unique_token(table):
    logger.info("Generating unique auth token")
    # Format: prefix_base64urlsafe_timestamp
    prefix = "swb"
    random_bytes = secrets.token_urlsafe(32)
    timestamp = hex(int(time.time()))[2:]
    token = f"{prefix}_{random_bytes}_{timestamp}"
    
    while True:
        response = table.get_item(Key={'token': token})
        if 'Item' not in response:
            logger.info("Unique token generated successfully")
            return token
        logger.info("Token collision detected, generating new token")
        random_bytes = secrets.token_urlsafe(32)
        token = f"{prefix}_{random_bytes}_{timestamp}"


def get_verification_code():
    logger.info("Generating verification code")
    code = str(random.randint(1000000, 9999999))
    return code


def last_auth_token_created_at(email: str, table) -> int:
    logger.info(f"Getting last auth token creation time for {email}")
    response = table.query(
        IndexName='email-created-index',
        KeyConditionExpression='email = :email',
        ScanIndexForward=False,  # Sort in descending order
        Limit=1,  # We only need the most recent record
        ExpressionAttributeValues={
            ':email': email
        }
    )
    items = response['Items']
    return items[0]['created'] if items else 0


def validate_email(email: str) -> bool:
    logger.info(f"Validating email: {email}")
    if len(email) == 0:
        logger.warning("Email validation failed: empty email")
        return False
    if len(email) > 254:
        logger.warning("Email validation failed: email too long")
        return False
    return email.count('@') == 1


def lambda_handler(event, context):
    logger.info("Starting auth token request handler")
    try:
        event_body = json.loads(event['body'])
    except Exception as e:
        logger.error(f"Failed to parse event body: {e}")
        return create_response(400, {'error': f'Error parsing event body: {e}'})
    email = event_body['email']
    if not validate_email(email):
        logger.warning(f"Invalid email: {email}")
        return create_response(400, {'error': 'Invalid email address'})
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('requested_auth_tokens')
    # if the last token was created within the last 5 minutes, return an error
    last_token_created_at = last_auth_token_created_at(email, table)
    if last_token_created_at > int(time.time()) - RETRY_TIME_SECONDS:
        logger.warning(f"Rate limit exceeded for email: {email}")
        return create_response(400, {
            'error': f'A new auth token can only be requested once every {RETRY_TIME_SECONDS} seconds - please wait before requesting another'
        })
    auth_token = generate_unique_token(table)
    verification_code = get_verification_code()
    timestamp = int(time.time())
    try:
        item = {
            'token': auth_token,
            'email': email,
            'verified': False,
            'last_used': timestamp,
            'created': timestamp,
            'verification_code': verification_code,
        }
        logger.info(f"Storing new auth token for email: {email}")
        table.put_item(Item=item)
        send_message(email, verification_code, "SWE-bench Auth Token Verification")
        logger.info("Auth token request completed successfully")
        return create_response(200, {
            'message': 'Auth token generated and email sent',
            'auth_token': auth_token
        })
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return create_response(500, {'error': INTERNAL_ERROR_MESSAGE.format(log_id=context.aws_request_id)})
