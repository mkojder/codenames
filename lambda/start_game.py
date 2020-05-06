import boto3
import datetime
import json
import random

from botocore.exceptions import ClientError

words = ['Hollywood', 'Well', 'Foot', 'New York', 'Spring', 'Court', 'Tube', 'Point', 'Tablet', 'Slip', 'Date', 'Drill', 'Lemon', 'Bell', 'Screen', 'Fair', 'Torch', 'State', 'Match', 'Iron', 'Block', 'France', 'Australia', 'Limousine', 'Stream', 'Glove', 'Nurse', 'Leprechaun', 'Play', 'Tooth', 'Arm', 'Bermuda', 'Diamond', 'Whale', 'Comic', 'Mammoth', 'Green', 'Pass', 'Missile', 'Paste', 'Drop', 'Pheonix', 'Marble', 'Staff', 'Figure', 'Park', 'Centaur', 'Shadow', 'Fish', 'Cotton', 'Egypt', 'Theater', 'Scale', 'Fall', 'Track', 'Force', 'Dinosaur', 'Bill', 'Mine', 'Turkey', 'March', 'Contract', 'Bridge', 'Robin', 'Line', 'Plate', 'Band', 'Fire', 'Bank', 'Boom', 'Cat', 'Shot', 'Suit', 'Chocolate', 'Roulette', 'Mercury', 'Moon', 'Net', 'Lawyer', 'Satellite', 'Angel', 'Spider', 'Germany', 'Fork', 'Pitch', 'King', 'Crane', 'Trip', 'Dog', 'Conductor', 'Part', 'Bugle', 'Witch', 'Ketchup', 'Press', 'Spine', 'Worm', 'Alps', 'Bond', 'Pan', 'Beijing', 'Racket', 'Cross', 'Seal', 'Aztec', 'Maple', 'Parachute', 'Hotel', 'Berry', 'Soldier', 'Ray', 'Post', 'Greece', 'Square', 'Mass', 'Bat', 'Wave', 'Car', 'Smuggler', 'England', 'Crash', 'Tail', 'Card', 'Horn', 'Capital', 'Fence', 'Deck', 'Buffalo', 'Microscope', 'Jet', 'Duck', 'Ring', 'Train', 'Field', 'Gold', 'Tick', 'Check', 'Queen', 'Strike', 'Kangaroo', 'Spike', 'Scientist', 'Engine', 'Shakespeare', 'Wind', 'Kid', 'Embassy', 'Robot', 'Note', 'Ground', 'Draft', 'Ham', 'War', 'Mouse', 'Center', 'Chick', 'China', 'Bolt', 'Spot', 'Piano', 'Pupil', 'Plot', 'Lion', 'Police', 'Head', 'Litter', 'Concert', 'Mug', 'Vacuum', 'Atlantis', 'Straw', 'Switch', 'Skyscraper', 'Laser', 'Scuba Diver', 'Africa', 'Plastic', 'Dwarf', 'Lap', 'Life', 'Honey', 'Horseshoe', 'Unicorn', 'Spy', 'Pants', 'Wall', 'Paper', 'Sound', 'Ice', 'Tag', 'Web', 'Fan', 'Orange', 'Temple', 'Canada', 'Scorpion', 'Undertaker', 'Mail', 'Europe', 'Soul', 'Apple', 'Pole', 'Tap', 'Mouth', 'Ambulance', 'Dress', 'Ice Cream', 'Rabbit', 'Buck', 'Agent', 'Sock', 'Nut', 'Boot', 'Ghost', 'Oil', 'Superhero', 'Code', 'Kiwi', 'Hospital', 'Saturn', 'Film', 'Button', 'Snowman', 'Helicopter', 'Loch Ness', 'Log', 'Princess', 'Time', 'Cook', 'Revolution', 'Shoe', 'Mole', 'Spell', 'Grass', 'Washer', 'Game', 'Beat', 'Hole', 'Horse', 'Pirate', 'Link', 'Dance', 'Fly', 'Pit', 'Server', 'School', 'Lock', 'Brush', 'Pool', 'Star', 'Jam', 'Organ', 'Berlin', 'Face', 'Luck', 'Amazon', 'Cast', 'Gas', 'Club', 'Sink', 'Water', 'Chair', 'Shark', 'Jupiter', 'Copper', 'Jack', 'Platypus', 'Stick', 'Olive', 'Grace', 'Bear', 'Glass', 'Row', 'Pistol', 'London', 'Rock', 'Van', 'Vet', 'Beach', 'Charge', 'Port', 'Disease', 'Palm', 'Moscow', 'Pin', 'Washington', 'Pyramid', 'Opera', 'Casino', 'Pilot', 'String', 'Night', 'Chest', 'Yard', 'Teacher', 'Pumpkin', 'Thief', 'Bark', 'Bug', 'Mint', 'Cycle', 'Telescope', 'Calf', 'Air', 'Box', 'Mount', 'Thumb', 'Antarctica', 'Trunk', 'Snow', 'Penguin', 'Root', 'Bar', 'File', 'Hawk', 'Battery', 'Compound', 'Slug', 'Octopus', 'Whip', 'America', 'Ivory', 'Pound', 'Sub', 'Cliff', 'Lab', 'Eagle', 'Genius', 'Ship', 'Dice', 'Hood', 'Heart', 'Novel', 'Pipe', 'Himalayas', 'Crown', 'Round', 'India', 'Needle', 'Shop', 'Watch', 'Lead', 'Tie', 'Table', 'Cell', 'Cover', 'Czech', 'Back', 'Bomb', 'Ruler', 'Forest', 'Bottle', 'Space', 'Hook', 'Doctor', 'Ball', 'Bow', 'Degree', 'Rome', 'Plane', 'Giant', 'Nail', 'Dragon', 'Stadium', 'Flute', 'Carrot', 'Wake', 'Fighter', 'Model', 'Tokyo', 'Eye', 'Mexico', 'Hand', 'Swing', 'Key', 'Alien', 'Tower', 'Poison', 'Cricket', 'Cold', 'Knife', 'Church', 'Board', 'Cloak', 'Ninja', 'Olympus', 'Belt', 'Light', 'Death', 'Stock', 'Millionaire', 'Day', 'Knight', 'Pie', 'Bed', 'Circle', 'Rose', 'Change', 'Cap', 'Triangle']
assassin_ratio = 1/25
card_ratio = 8/25

def start_game(event, context):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('Games')
    body = json.loads(event['body'])
    game_id = body['id']
    user = body['user']
    connection_id = event['requestContext']['connectionId']
    width = body['width']
    height = body['height']
    if width < 4 or width > 9 or height < 4 or height > 9:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": f'Board height/width must each be between 4 and '})
        }
    word_list = []
    identities = []
    revealed = []
    all_words = set([])
    goes_first = random.choice(('red', 'blue'))
    total_cards = width * height
    base_cards_count = int(round(card_ratio * total_cards))
    goes_first_cards_count = base_cards_count + 1
    identity_pool = ['assassin'] * (int(round(assassin_ratio * total_cards))) + ['red', 'blue'] * (base_cards_count)
    identity_pool += [goes_first]
    identity_pool += ['neutral'] * (total_cards - len(identity_pool))
    for x in range(height):
        cur = []
        cur_identities = []
        word_list.append(cur)
        identities.append(cur_identities)
        revealed.append([False] * width)
        for y in range(width):
            word = random.choice(words)
            while word in all_words:
                word = random.choice(words)
            cur.append(word)
            all_words.add(word)
            identity_choice = random.choice(identity_pool)
            identity_pool.remove(identity_choice)
            cur_identities.append(identity_choice)
            
    result = table.get_item(Key={
        'id': game_id
    })
    result = result['Item']
    red_team = result['red_team']
    blue_team = result['blue_team']
    for player in result['user_name_list']:
        # Consider adding back later
        # if not table.get_item(Key={'id': 'connection_id-' + result['connection_info'][player]})['Item']['is_active']:
        #     continue
        if player not in red_team and player not in blue_team:
            if len(red_team) < len(blue_team):
                red_team.append(player)
            else:
                blue_team.append(player)
                
    if len(result['red_team']) < 2 or len(result['blue_team']) < 2:
        return {
            'statusCode': 409,
            'body': json.dumps({"error": f'Not enough active players on each team to play yet'})
        }
    if 'red_spymaster' in result and result['red_spymaster'].strip() != '':
        red_spymaster = result['red_spymaster']
    else:
        red_spymaster = random.choice(red_team)
        
    if 'blue_spymaster' in result and result['blue_spymaster'].strip() != '':
        blue_spymaster = result['blue_spymaster']
    else:
        blue_spymaster = random.choice(blue_team)
    
    try:
        result = table.update_item(
            Key={
                'id': game_id,
            },
            UpdateExpression="SET game_state = :a, words = :b, red_team = :c, blue_team = :d, red_spymaster = :e, blue_spymaster = :f, goes_first = :g, tile_identities = :h, game_start_time = :i, last_update_time = :i, red_clues = :j, blue_clues = :k, turn = :l, revealed = :m, red_count_left = :n, blue_count_left = :o, guess_num = :p",
            ConditionExpression="game_state = :t and user_name_list[0] = :v and connection_info.#u = :u and id = :id",
            ExpressionAttributeNames={
                '#u': user
            },
            ExpressionAttributeValues={
                ':a': 'in_game',
                ':b': word_list,
                ':c': red_team,
                ':d': blue_team,
                ':e': red_spymaster,
                ':f': blue_spymaster,
                ':g': goes_first,
                ':h': identities,
                ':i': datetime.datetime.utcnow().isoformat(),
                ':j': [],
                ':k': [],
                ':l': goes_first + '_spymaster',
                ':m': revealed,
                ':n': base_cards_count if goes_first == 'blue' else goes_first_cards_count,
                ':o': base_cards_count if goes_first == 'red' else goes_first_cards_count,
                ':p': 0,
                ':t': 'waiting_room',
                ':u': connection_id,
                ':v': user,
                ':id': game_id
            },
            ReturnValues="ALL_NEW"
        )
    except ClientError as e:
        print(str(e))
        return {
            'statusCode': 409,
            'body': json.dumps({"error": f'This game is not in the correct state to transition to in_game'})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }
