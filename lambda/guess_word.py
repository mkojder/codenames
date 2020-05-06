import boto3
import datetime
import json

from botocore.exceptions import ClientError


def guess_word(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Games')
    body = json.loads(event['body'])
    game_id = body['id']
    user = body['user']
    connection_id = event['requestContext']['connectionId']
    
    guess = body['guess'] if 'guess' in body else None
    
    result = table.get_item(Key={
        'id': game_id
    })['Item']
    
    if user in (result['red_spymaster'], result['blue_spymaster']):
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'Unable to make turn as player is spymaster'})
        }
    
    if result['turn'] == 'red_team_guess':
        red_turn = True
    elif result['turn'] == 'blue_team_guess':
        red_turn = False
    else:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'This action is not valid'})
        }
    
    if result['connection_info'][user] != connection_id:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'User and connection info does not match up'})
        }
        
    if (red_turn and user not in result['red_team']) or (not red_turn and user not in result['blue_team']) or user == result['red_spymaster'] or user == result['blue_spymaster']:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'You are not authorized to make a guess'})
        }
    
    winner = None
    new_turn = result['turn']
    guess_num = result['guess_num']
    red_count_left = result['red_count_left']
    blue_count_left = result['blue_count_left']
    game_state = result['game_state']
    
    if guess is None:
        new_turn = 'blue_spymaster' if red_turn else 'red_spymaster'
        try:
            table.update_item(
                Key={
                    'id': game_id,
                },
                UpdateExpression=f"SET turn = :a, last_update_time = :i",
                ConditionExpression=f"connection_info.#u = :u and turn = :z and id = :id",
                ExpressionAttributeNames={
                    '#u': user
                },
                ExpressionAttributeValues={
                    ':a': new_turn,
                    ':i': datetime.datetime.utcnow().isoformat(),
                    ':u': connection_id,
                    ':z': 'red_team_guess' if red_turn else 'blue_team_guess',
                    ':id': game_id
                },
            )
        except ClientError as e:
            print(str(e))
            return {
                'statusCode': 409,
                'body': json.dumps({"error": 'Unable to make turn'})
            }
        
    else:
        found_at = None
        for i, rows in enumerate(result['words']):
            for j, val in enumerate(rows):
                if guess == val and not result['revealed'][i][j]:
                    found_at = (i, j)
                    break
            if found_at is not None:
                break
        
        identity = result['tile_identities'][found_at[0]][found_at[1]]
        if identity == 'assassin':
            new_turn = 'game_over'
            game_state = 'post_game'
            winner = 'blue_team' if red_turn else 'red_team'
            
        elif identity == 'red':
            red_count_left -= 1
            if red_count_left == 0:
                new_turn = 'game_over'
                game_state = 'post_game'
                winner = 'red_team'
            else:
                if red_turn:
                    item = result['red_clues'][-1][1]
                    if isinstance(item, str):
                        item = int(item)
                    if guess_num < item:
                        guess_num += 1
                    else:
                        new_turn = 'blue_spymaster'
                else:
                    new_turn = 'red_spymaster'
    
        elif identity == 'blue':
            blue_count_left -= 1
            if blue_count_left == 0:
                new_turn = 'game_over'
                game_state = 'post_game'
                winner = 'blue_team'
            else:
                if not red_turn:
                    item = result['blue_clues'][-1][1]
                    if isinstance(item, str):
                        item = int(item)
                    if guess_num < item:
                        guess_num += 1
                    else:
                        new_turn = 'red_spymaster'
                else:
                    new_turn = 'blue_spymaster'
        else:
            if red_turn:
                new_turn = 'blue_spymaster'
            else:
                new_turn = 'red_spymaster'
        
    
        try:
            table.update_item(
                Key={
                    'id': game_id,
                },
                UpdateExpression=f"SET revealed[{found_at[0]}][{found_at[1]}] = :t, turn = :a, guess_num = :b, red_count_left = :c, blue_count_left = :d, winner = :e, game_state = :g, last_update_time = :i",
                ConditionExpression=f"connection_info.#u = :u and turn = :z and revealed[{found_at[0]}][{found_at[1]}] = :f and id = :id",
                ExpressionAttributeNames={
                    '#u': user
                },
                ExpressionAttributeValues={
                    ':a': new_turn,
                    ':b': guess_num,
                    ':c': red_count_left,
                    ':d': blue_count_left,
                    ':e': ' ' if winner is None else winner,
                    ':f': False,
                    ':t': True,
                    ':g': game_state,
                    ':i': datetime.datetime.utcnow().isoformat(),
                    ':u': connection_id,
                    ':z': 'red_team_guess' if red_turn else 'blue_team_guess',
                    ':id': game_id
                },
            )
        except ClientError as e:
            print(str(e))
            return {
                'statusCode': 409,
                'body': json.dumps({"error": 'Unable to make turn'})
            }
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }
