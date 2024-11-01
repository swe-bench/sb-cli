import json
import boto3
import uuid
import time
import smtplib
import random
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_fastmail_password():
    secret_name = "swebm/smtp-fastmail-password"
    region_name = "us-east-2"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        logger.error(f"Error getting secret value: {str(e)}")
        raise e
    secret = json.loads(get_secret_value_response['SecretString'])
    return secret["password"]


def send_message(to_addr, msg, subject):
    username = "carlos@swerl.ai"
    from_addr = "evals@swebench.com"
    password = get_fastmail_password()
    logger.info(f"Sending email to {to_addr} with subject: {subject}")
    try:
        smtp = smtplib.SMTP_SSL('smtp.fastmail.com', port=465)
        smtp.login(username, password)
        msg_root = MIMEMultipart()
        msg_root['Subject'] = subject
        msg_root['From'] = from_addr
        msg_root['To'] = to_addr
        msg_alternative = MIMEMultipart('alternative')
        msg_root.attach(msg_alternative)
        msg_alternative.attach(MIMEText(msg))
        smtp.sendmail(from_addr, to_addr, msg_root.as_string())
        smtp.quit()
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise e


def get_verification_code():
    code = str(random.randint(1000000, 9999999))
    return code


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        event_body = json.loads(event['body'])
    except Exception as e:
        logger.error(f"Error parsing event body: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Error parsing event body: {e}'})
        }
    try:
        email = event_body['email']
        logger.info(f"Processing request for email: {email}")
    except KeyError as e:
        logger.error(f"Missing required key in event body: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Body has keys: {event_body.keys()} - missing key: {e}'})
        }
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('requested_auth_tokens')

    success_message = 'If an auth token exists for this email, you will receive an email with a verification code to remove it.'

    # Check number of existing tokens for this email
    try:
        logger.info(f"Scanning for existing tokens for email: {email}")
        response = table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        # we don't actually delete tokens (just de-verify them) so filter for verified
        existing_tokens = [item for item in response['Items'] if item['verified']]
        logger.info(f"Found {len(existing_tokens)} verified tokens")
        
        if len(existing_tokens) == 0:
            logger.info("No verified tokens found, returning success message")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': success_message
                })
            }

        removal_verification_code = get_verification_code()
        timestamp = int(time.time())
        logger.info(f"Generated removal verification code: {removal_verification_code}")

        # get item from existing tokens
        for item in existing_tokens:
            # add requested deletion verification code and timestamp
            item = {
                **item,
                'removal_verification_code': removal_verification_code,
                'requested_removal': timestamp,
            }
            logger.info(f"Updating token {item['token']} with removal info")
            table.put_item(Item=item)
        email_body = f"""
        Here's your verification code to remove your auth token: {removal_verification_code}

        If you did not request to remove your auth token, you can ignore this email.
        """
        send_message(email, email_body, "SWE-bench Auth Token Removal Verification")
        logger.info("Successfully processed removal request")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': success_message
            })
        }
    
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error removing auth token - please email support@swebench.com'
        }
