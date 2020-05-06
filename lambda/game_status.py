import boto3
import json

from botocore.exceptions import ClientError


def status_in_game(result, user):
    ret = {
        'blue_clues': result['blue_clues'],
        'blue_count_left': result['blue_count_left'],
        'blue_spymaster': result['blue_spymaster'],
        'blue_team': result['blue_team'],
        'game_state': result['game_state'],
        'guess_num': result['guess_num'],
        'id': result['id'],
        'red_clues': result['red_clues'],
        'red_count_left': result['red_count_left'],
        'red_spymaster': result['red_spymaster'],
        'red_team': result['red_team'],
        'revealed': result['revealed'],
        'turn': result['turn'],
        'url': result['url'],
        'words': result['words']
    }
    if user in (result['red_spymaster'], result['blue_spymaster']):
        ret['tile_identities'] = result['tile_identities']
    return ret
    
def status_in_waiting_room(result):
    return {
        'blue_team': result['blue_team'],
        'blue_spymaster': result['blue_spymaster'] if 'blue_spymaster' in result else None,
        'game_state': result['game_state'],
        'id': result['id'],
        'red_team': result['red_team'],
        'red_spymaster': result['red_spymaster'] if 'red_spymaster' in result else None,
        'revealed': result['revealed'],
        'turn': result['turn'],
        'url': result['url'],
        'user_name_list': result['user_name_list']
    }
    
def status_in_game_over(result):
    return {
        'blue_clues': result['blue_clues'],
        'blue_count_left': result['blue_count_left'],
        'blue_spymaster': result['blue_spymaster'],
        'blue_team': result['blue_team'],
        'game_state': result['game_state'],
        'id': result['id'],
        'red_clues': result['red_clues'],
        'red_count_left': result['red_count_left'],
        'red_spymaster': result['red_spymaster'],
        'red_team': result['red_team'],
        'revealed': result['revealed'],
        'url': result['url'],
        'words': result['words']
    }

def game_status(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Games')
    body = json.loads(event['body'])
    game_id = body['id']
    user = body['user']
    connection_id = event['requestContext']['connectionId']
    result = table.get_item(Key={
        'id': game_id
    })['Item']
    
    if user not in result['user_name_list'] or connection_id != result['connection_info'][user]:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'You are not authorized to get status of this game or your connection id and user do not match'})
        }
    
    if result['game_status'] == 'in_game':
        status = status_in_game(result, user)
    elif result['game_status'] == 'waiting_room':
        status = status_in_waiting_room(result)
    elif result['game_status'] == 'game_over':
        status = status_in_game_over(result)
    else:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'Game status in unrecognized state'})
        }
        
    return {
        'statusCode': 200,
        'body': json.dumps(status)
    }
