import asyncio
import functools
import json
import os
import requests

from aws_requests_auth.aws_auth import AWSRequestsAuth

def mask_unrevealed(tile_identities, revealed):
    res = []
    for i, row in enumerate(tile_identities):
        new_row = []
        for j, identity in enumerate(row):
            if revealed[i][j]:
                new_row.append(identity)
            else:
                new_row.append(None)
        res.append(new_row)
    return res

def status_in_game(result, user):
    ret = {
        'blue_clues': result['blue_clues'],
        'blue_count_left': result['blue_count_left'],
        'blue_spymaster': result['blue_spymaster'],
        'blue_team': result['blue_team'],
        'game_state': result['game_state'],
        'guess_num': result['guess_num'],
        'id': result['id'],
        'last_update_time': result['last_update_time'],
        'red_clues': result['red_clues'],
        'red_count_left': result['red_count_left'],
        'red_spymaster': result['red_spymaster'],
        'red_team': result['red_team'],
        'revealed': result['revealed'],
        'tile_identities': mask_unrevealed(result['tile_identities'], result['revealed']),
        'turn': result['turn'],
        'url': result['url'],
        'words': result['words'],
        'player': user
    }
    if user in (result['red_spymaster'], result['blue_spymaster']):
        ret['tile_identities'] = result['tile_identities']
    return ret
    
def status_in_waiting_room(result, user):
    return {
        'blue_team': result['blue_team'],
        'blue_spymaster': result['blue_spymaster'] if 'blue_spymaster' in result else None,
        'game_state': result['game_state'],
        'id': result['id'],
        'last_update_time': result['last_update_time'],
        'red_team': result['red_team'],
        'red_spymaster': result['red_spymaster'] if 'red_spymaster' in result else None,
        'url': result['url'],
        'user_name_list': result['user_name_list'],
        'player': user
    }
    
def status_in_game_over(result):
    return {
        'blue_clues': result['blue_clues'],
        'blue_count_left': result['blue_count_left'],
        'blue_spymaster': result['blue_spymaster'],
        'blue_team': result['blue_team'],
        'game_state': result['game_state'],
        'id': result['id'],
        'last_update_time': result['last_update_time'],
        'red_clues': result['red_clues'],
        'red_count_left': result['red_count_left'],
        'red_spymaster': result['red_spymaster'],
        'red_team': result['red_team'],
        'revealed': result['revealed'],
        'url': result['url'],
        'words': result['words']
    }
    
def convert_record(record):
    repl = {}
    for k, v in record.items():
        t = list(v.keys())[0]
        v = list(v.values())[0]
        if t == 'BOOL':
            repl[k] = v
        elif t == 'N':
            repl[k] = float(v)
        elif t == 'S':
            repl[k] = v
        elif t == 'B':
            raise NotImplementedError()
        elif t == 'SS':
            raise NotImplementedError()
        elif t == 'BS':
            raise NotImplementedError()
        elif t == 'NS':
            raise NotImplementedError()
        elif t == 'L':
            repl[k] = convert_list(v)
        elif t == 'M':
            repl[k] = convert_record(v)
    return repl
    
def convert_list(record):
    repl = []
    for t, v in [(list(r.keys())[0], list(r.values())[0]) for r in record]:
        if t == 'BOOL':
            repl.append(v)
        elif t == 'N':
            repl.append(float(v))
        elif t == 'S':
            repl.append(v)
        elif t == 'B':
            raise NotImplementedError()
        elif t == 'SS':
            raise NotImplementedError()
        elif t == 'BS':
            raise NotImplementedError()
        elif t == 'NS':
            raise NotImplementedError()
        elif t == 'L':
            repl.append(convert_list(v))
        elif t == 'M':
            repl.append(convert_record(v))
    return repl
        

async def handle_record(record, auth):
    loop = asyncio.get_event_loop()
    all_tasks = []
    print(record)
    users = record['user_name_list']
    if record['game_state'] == 'in_game':
        statuses = []
        for user in users:
            if user in (record['red_spymaster'], record['blue_spymaster']):
                statuses.append((user, status_in_game(record, user)))
            else:
                statuses.append((user, status_in_game(record, user)))
        

    elif record['game_state'] == 'waiting_room':
        statuses = []
        for user in users:
            statuses.append((user, status_in_waiting_room(record, user)))

    elif record['game_state'] == 'post_game':
        status = status_in_game_over(record)
        statuses = [(user, status) for user in users]
    else:
        raise ValueError("Game state not recognized")
        
    for user, status in statuses:
        if user not in record['connection_info']:
            continue
        connection_id = record['connection_info'][user]
        all_tasks.append(
            loop.run_in_executor(None, 
                                 functools.partial(requests.post, 
                                                   f'https://0ppn9ycig5.execute-api.us-east-1.amazonaws.com/alpha/@connections/{connection_id}', 
                                                   json=status,
                                                   auth=auth)))
        
    results = await asyncio.gather(*all_tasks)
        

def process_db_change(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_process_db_change(event, context))

async def async_process_db_change(event, context):
    aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
    aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
    aws_session_token = os.environ['AWS_SESSION_TOKEN']

    auth = AWSRequestsAuth(aws_access_key=aws_access_key_id,
                           aws_secret_access_key=aws_secret_access_key,
                           aws_token=aws_session_token,
                           aws_host='0ppn9ycig5.execute-api.us-east-1.amazonaws.com',
                           aws_region='us-east-1',
                           aws_service='execute-api')
    latest_record = {}
    for i, record in enumerate(event['Records']):
        latest_record[record['dynamodb']['Keys']['id']['S']] = i
        
    all_tasks = []
    for game_id, ind in latest_record.items():
        if 'NewImage' not in event['Records'][ind]['dynamodb']:
            continue
        if not event['Records'][ind]['dynamodb']['NewImage']['id']['S'].startswith('game'):
            continue
        record = convert_record(event['Records'][ind]['dynamodb']['NewImage'])
        try:
            all_tasks.append(asyncio.create_task(handle_record(record, auth)))
        except ValueError as e:
            return {
                'statusCode': 409,
                'body': json.dumps('Game state not recognized')
            }
        
    await asyncio.gather(*all_tasks)
        
        
        
    return {
        'statusCode': 200,
        'body': json.dumps('success')
    }
