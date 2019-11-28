import json
import os
import random
import bottle
import pdb
import unicodedata

from api import ping_response, start_response, move_response, end_response

# Directions
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'
UP = 'up'

BOARD_HEIGHT = 0
BOARD_WIDTH = 0
CURRENT_POS = {}
FOOD = {}
OPPOSITES = { UP: DOWN, LEFT: RIGHT, DOWN: UP, RIGHT: LEFT }
PREV_DIRECTION = None
ROYAL_PYTHON = 'royal-python'
SNAKE_ENEMIES = []

@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    '''

@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')

@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()

def set_closest_food(foods):
    global FOOD

    min_distance = None
    closest_food = None

    for food in foods:
        distance = abs(food['x'] - CURRENT_POS['x']) + abs(food['y'] - CURRENT_POS['y'])
        if (min_distance is None or distance < min_distance):
            min_distance = distance
            closest_food = food
    
    FOOD = closest_food

@bottle.post('/start')
def start():
    data = bottle.request.json

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    global BOARD_HEIGHT
    global BOARD_WIDTH
    global SNAKE_ENEMIES
    global CURRENT_POS

    BOARD_HEIGHT = data['board']['height'] - 1
    BOARD_WIDTH = data['board']['width'] - 1
    SNAKE_ENEMIES = data['board']['snakes']
    
    CURRENT_POS = data['you']['body'][0]

    # pdb.set_trace()

    color = "#ffbf00"
    head_type = 'fang'
    tail_type = 'fat-rattle'

    set_closest_food(data['board']['food'])

    return start_response(color, head_type, tail_type)

def get_next_position(direction):
    if direction == UP:
        return { 'x': CURRENT_POS['x'], 'y': CURRENT_POS['y'] - 1 }
    if direction == DOWN:
        return { 'x': CURRENT_POS['x'], 'y': CURRENT_POS['y'] + 1 }
    if direction == LEFT:
        return { 'x': CURRENT_POS['x'] - 1, 'y': CURRENT_POS['y'] }
    if direction == RIGHT:
        return { 'x': CURRENT_POS['x'] + 1, 'y': CURRENT_POS['y'] }

def avoid_enemies(possible_directions):
    for direction in possible_directions:
        # Remove direction if an enemy is there
        next_position = get_next_position(direction)
        for snake in SNAKE_ENEMIES:
            if next_position in snake['body']:
                possible_directions.remove(direction)

    return possible_directions

def get_best_next_direction(possible_directions):
    if FOOD['x'] < CURRENT_POS['x'] and LEFT in possible_directions:
        return LEFT
    elif FOOD['x'] > CURRENT_POS['x'] and RIGHT in possible_directions:
        return RIGHT
    elif FOOD['y'] < CURRENT_POS['y'] and UP in possible_directions:
        return UP
    elif FOOD['y'] > CURRENT_POS['y'] and DOWN in possible_directions:
        return DOWN

def get_next_direction():
    global PREV_DIRECTION

    possible_directions = [DOWN, LEFT, RIGHT, UP]
    
    # Don't crash into the walls
    if (CURRENT_POS['x'] == BOARD_WIDTH):
        possible_directions.remove(RIGHT)
    elif (CURRENT_POS['x'] == 0):
        possible_directions.remove(LEFT)
    if (CURRENT_POS['y'] == BOARD_WIDTH):
        possible_directions.remove(DOWN)
    elif(CURRENT_POS['y'] == 0):
        possible_directions.remove(UP)

    # Don't crash into yourself
    if PREV_DIRECTION:
        possible_directions.remove(OPPOSITES[PREV_DIRECTION])
    
    # Don't crash into snake enemies
    possible_directions = avoid_enemies(possible_directions)

    direction = get_best_next_direction(possible_directions)

    PREV_DIRECTION = direction

    return direction


@bottle.post('/move')
def move():
    data = bottle.request.json
    # print(json.dumps(data))

    """
    TODO: Using the data from the endpoint request object, your
            snake AI must choose a direction to move in.
    """
    global SNAKE_ENEMIES
    global CURRENT_POS

    # Set closest food
    set_closest_food(data['board']['food'])

    # Update snake enemies
    SNAKE_ENEMIES = data['board']['snakes']

    # Update current position
    CURRENT_POS = data['you']['body'][0]

    direction = get_next_direction()

    # directions = ['up', 'down', 'left', 'right']
    # direction = random.choice(directions)

    print('************DIRECTION************')
    print(direction)

    return move_response(direction)

@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print(json.dumps(data))

    return end_response()

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )
