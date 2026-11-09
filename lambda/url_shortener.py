import json
import os
import time
import hashlib
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', ''))

def lambda_handler(event, context):
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')

    if http_method == 'POST':
        body_raw = event.get('body') or '{}'
        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON"})}

        original_url = body.get('url')
        if not original_url:
            return {"statusCode": 400, "body": json.dumps({"error": "url is required"})}

        short_key = hashlib.md5(original_url.encode()).hexdigest()[:6]
        expires_at = int(time.time()) + 15 * 60

        item = {
            'short_key': short_key,
            'original_url': original_url,
            'created_at': int(time.time()),
            'expires_at': expires_at,
        }

        table.put_item(Item=item)

        stage = event.get('requestContext', {}).get('stage', '')
        domain = event.get('headers', {}).get('Host', '')
        base_url = f"https://{domain}/{stage}" if stage and domain else ""
        shortened_url = f"{base_url}/{short_key}" if base_url else f"/{short_key}"

        response_body = {
            "short_key": short_key,
            "shortened_url": shortened_url,
            "expires_at": expires_at
            
        }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_body)
        }

    elif http_method in ('GET', 'HEAD'):
        short_key = path.strip('/')
        if not short_key:
            return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}

        resp = table.get_item(Key={'short_key': short_key})
        item = resp.get('Item')

        if not item:
            return {"statusCode": 404, "body": json.dumps({"message": "Not Found"})}

        current_time = int(time.time())
        if 'expires_at' in item and current_time > int(item['expires_at']):
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Link expired"})
            }

        return {
            "statusCode": 301,
            "headers": {
                "Location": item['original_url']
            },
            "body": ""
        }

    return {"statusCode": 405, "body": "Method Not Allowed"}