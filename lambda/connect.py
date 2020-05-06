import boto3
import datetime
import json

from botocore.exceptions import ClientError

def connect_handler(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Games')
    connection_id = event['requestContext']['connectionId']
    try:
        table.update_item(
            Key={
                'id': 'connection_id-' + connection_id,
            },
            UpdateExpression="SET is_connected = :t, connect_time = :a",
            ExpressionAttributeValues={
                ':a': datetime.datetime.utcnow().isoformat(),
                ':t': True
            }
        )
    except ClientError as e:
        print(str(e))
        return {
            'statusCode': 409,
            'body': json.dumps({"error": f'Could not properly connect player'})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps(connection_id)
    }
