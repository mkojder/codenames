if 'is_active' in result and result['is_active']:
        game_result = table.get_item(
            Key={
                'id': result['active_game_id']
            }
        )['Item']
        uname = result['user_name']
        user_list = game_result['user_name_list']
        if game_result['game_state'] == 'waiting_room':
            user_list.remove(uname)
        red_spymaster = game_result['red_spymaster'] if 'red_spymaster' in game_result else ' '
        blue_spymaster = game_result['blue_spymaster'] if 'blue_spymaster' in game_result else ' '
        if uname in game_result['red_team'] and red_spymaster == uname:
            if game_result['game_state'] == 'in_game':
                red_team = game_result['red_team']
                red_team.remove(uname)
                red_spymaster = random.choice(red_team)
            elif game_result['game_state'] == 'waiting_room':
                red_spymaster = ' '
        if uname in game_result['blue_team'] and blue_spymaster == uname:
            if game_result['game_state'] == 'in_game':
                blue_team = game_result['blue_team']
                blue_team.remove(uname)
                blue_spymaster = random.choice(blue_team)
            elif game_result['game_state'] == 'waiting_room':
                blue_spymaster = ' '
        table.update_item(
            Key={
                'id': result['active_game_id'],
            },
            UpdateExpression="SET red_spymaster = :a, blue_spymaster = :b, user_name_list = :c REMOVE connection_info.#a",
            ExpressionAttributeNames={
                '#a': connection_id
            },
            ExpressionAttributeValues={
                ':a': red_spymaster,
                ':b': blue_spymaster,
                ':c': user_list
            }
        )
           