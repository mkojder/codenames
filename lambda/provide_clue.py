import boto3
import datetime
import json

from botocore.exceptions import ClientError

def provide_clue(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Games')
    body = json.loads(event['body'])
    game_id = body['id']
    user = body['user']
    connection_id = event['requestContext']['connectionId']
    word = body['word']
    times = body['times']

    
    result = table.get_item(Key={
        'id': game_id
    })['Item']
    
    if result['turn'] == 'red_spymaster':
        spymaster = result['red_spymaster']
        red_turn = True
    elif result['turn'] == 'blue_spymaster':
        spymaster = result['blue_spymaster']
        red_turn = False
    else:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": 'This action is not valid'})
        }
    
    try:
        table.update_item(
            Key={
                'id': game_id,
            },
            UpdateExpression="SET #c = list_append(#c, :b), turn = :a, guess_num = :d, last_update_time = :i",
            ConditionExpression="#s = :c and connection_info.#u = :u and turn = :t and id = :id",
            ExpressionAttributeNames={
                '#c': 'red_clues' if red_turn else 'blue_clues',
                '#s': 'red_spymaster' if red_turn else 'blue_spymaster',
                '#u': spymaster
            },
            ExpressionAttributeValues={
                ':a': 'red_team_guess' if red_turn else 'blue_team_guess',
                ':b': [[word, times]],
                ':c': user,
                ':d': 0,
                ':i': datetime.datetime.utcnow().isoformat(),
                ':u': connection_id,
                ':t': 'red_spymaster' if red_turn else 'blue_spymaster',
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
