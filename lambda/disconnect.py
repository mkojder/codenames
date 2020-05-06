import boto3
import datetime
import json
import random

from botocore.exceptions import ClientError

def disconnect_handler(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Games')
    connection_id = event['requestContext']['connectionId']
    result = table.get_item(
        Key={
            'id': 'connection_id-' + connection_id
        }
    )['Item']
    if 'is_active' in result and result['is_active']:
        table.update_item(
            Key={
                'id': result['active_game_id'],
            },
            UpdateExpression="REMOVE #a.#b",
            ExpressionAttributeNames={
                '#a': 'connection_info',
                '#b': result['user_name']
            }
        )
            
    try:
        table.update_item(
            Key={
                'id': 'connection_id-' + connection_id,
            },
            UpdateExpression="SET is_connected = :f, is_active = :f, disconnect_time = :a",
            ExpressionAttributeValues={
                ':a': datetime.datetime.utcnow().isoformat(),
                ':f': False
            }
        )
    except ClientError as e:
        print(str(e))
        return {
            'statusCode': 409,
            'body': json.dumps({"error": f'Could not properly disconnect player'})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Disconnect success')
    }
