import boto3
import datetime
import json

from botocore.exceptions import ClientError


def claim_team(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Games')
    body = json.loads(event['body'])
    game_id = body['id']
    user = body['user']
    team = body['team']
    connection_id = event['requestContext']['connectionId']
    request_spymaster = body['spymaster'] if 'spymaster' in body else False
    
    if team not in ('red', 'blue', 'random'):
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'Team does not exist'})
        }
        
    if team == 'random' and request_spymaster:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'Cannot be unassigned team and request spymaster'})
        }
        
    result = table.get_item(
        Key={
            'id': game_id
        }
    )['Item']
    
    if result['connection_info'][user] != connection_id:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'User and connection info does not match up'})
        }
    
    orig_blue_team = result['blue_team']
    orig_red_team = result['red_team']
    
    blue_team = list(orig_blue_team)
    red_team = list(orig_red_team)
    if team == 'random':
        if user in red_team:
            red_team.remove(user)
        if user in blue_team:
            blue_team.remove(user)
    elif team == 'blue':
        if user in red_team:
            red_team.remove(user)
        if user not in blue_team:
            blue_team.append(user)
    else:
        if user not in red_team:
            red_team.append(user)
        if user in blue_team:
            blue_team.remove(user)
            
    eav = {
        ':a': red_team,
        ':b': blue_team,
        ':c': orig_red_team,
        ':d': orig_blue_team,
        ':id': game_id
    }
    
    ue = "SET red_team = :a, blue_team = :b"
    
    if request_spymaster and team == 'red' and ('red_spymaster' not in result or result['red_spymaster'].strip() == ''):
        ue += ', red_spymaster = :e'
        eav[':e'] = user
    elif request_spymaster and team == 'blue' and ('blue_spymaster' not in result or result['blue_spymaster'].strip() == ''):
        ue += ', blue_spymaster = :e'
        eav[':e'] = user
    
    if 'red_spymaster' in result and result['red_spymaster'] == user and user not in red_team:
        ue += ' REMOVE red_spymaster'
    elif 'blue_spymaster' in result and result['blue_spymaster'] == user and user not in blue_team:
        ue += ' REMOVE blue_spymaster'
    
    try:
        result = table.update_item(
            Key={
                'id': game_id,
            },
            UpdateExpression=ue,
            ConditionExpression="red_team = :c and blue_team = :d and id = :id",
            ExpressionAttributeValues=eav
        )
    except ClientError as e:
        print('Game state changed between get and set')
        return {
                'statusCode': 409,
                'body': json.dumps({"error": 'Game state changed between get and set'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps("Success")
    }
