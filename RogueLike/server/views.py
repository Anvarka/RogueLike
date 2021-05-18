import json
import random
import requests
from rest_framework.decorators import api_view
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from enum import Enum
from server import models
from server.characters import AggressiveEnemy, Player, CharacterEncoder

from server.characters import PassiveEnemy


current_players = {}
current_map = None


class PlayerNotifier():
    def __init__(self):
        self.last_notified = -1

    def notifiy_active_next(self):
        self.last_notified = (self.last_notified + 1) % len(current_players) 
        notify_id = list(current_players.keys())[self.last_notified]
        print("NOTIFY ACTIVE: " + notify_id)
        req = requests.post(current_players[notify_id] + '/state', params={'value': 'ACTIVE'})
        print(req.url)


notifier = PlayerNotifier()


class Move(Enum):
    up = "up"
    down = "down"
    left = "left"
    right = "right"


@api_view(['POST'])
def get_map(request):
    """
    function for getting map
    """
    request_message = json.loads(request.body)
    if not session_exists():
        return HttpResponse("Вы еще не зарегистрированы")
    user_id = request_message["user_id"]
    user_info = models.Session.objects.get()
    response_message = {
        "walls": user_info.walls,
        "stairs": user_info.stairs,
        "players": user_info.players,
        "enemies": user_info.enemies,
        "game_over": user_info.game_over
    }
    return JsonResponse(response_message, encoder=CharacterEncoder, safe=False)


@api_view(['POST'])
def player_move(request):
    """
    Change the position of the player depending on the command
    """
    request_message = json.loads(request.body)
    user_id = request_message["user_id"]
    direction = request_message["direction"]
    user_info = models.Session.objects.get()
    player = None
    for pl in user_info.players:
        if pl.user_id == user_id:
            player = pl
            break

    player.move(direction, user_info)

    if player.cur_pos == user_info.stairs:
        walls, stairs, enemies = generate_map()
        user_info.walls = walls
        user_info.stairs = stairs
        user_info.enemies = enemies
        for (i, pl) in enumerate(user_info.players):
            pl.cur_pos = [0, i]
        # user_info.cur_pos = [0, 0]

    # TODO: enemies move too much now
    for enemy in user_info.enemies:
        enemy.move(enemy.get_next_move(user_info), user_info)

    response_message = {
        "walls": user_info.walls,
        "players": user_info.players,
        "stairs": user_info.stairs,
        "enemies": user_info.enemies,
        "game_over": user_info.game_over
    }
    user_info.save()
    
    req = requests.post(current_players[user_id] + '/state', params={'value': 'WAIT'})
    notifier.notifiy_active_next()

    return JsonResponse(response_message, encoder=CharacterEncoder, safe=False)


@api_view(['POST'])
def connect(request):
    """
    Connect with server
    Register of user
    """
    request_message = json.loads(request.body)
    user_id = request_message["user_id"]
    user_url = request.build_absolute_uri('/').strip('/').rsplit(':', 1)[0]
    if user_id == 'was':
        user_url = user_url + ':1235'
    else:
        user_url = user_url + ':1234'
    print("USER_URL: " + user_url)

    current_players[user_id] = user_url
    response = None
    if not session_exists():
        walls, stairs, enemies = generate_map()
        models.Session.objects.create(walls=walls,stairs=stairs,players=[Player(0, 0, user_id)], enemies=enemies, game_over=False)
    else:
        session = models.Session.objects.get()
        if user_id not in [pl.user_id for pl in session.players]:
            session.players.append(Player(0, 0, user_id))
        session.save()

    response = HttpResponse(f"Поздравляю, вы зарегистрированы, {user_id}")

    if len(current_players) == 1:
        init_state = 'ACTIVE'
    else:
        init_state = 'WAIT'
    req = requests.post(user_url + '/state', params={'value': init_state})

    return response


def session_exists():
    try:
        session = models.Session.objects.get()
        return True
    except ObjectDoesNotExist:
        return False


def is_user_new(user_id):
    """
    Check if the user is in the database
    """
    try:
        user_and_map = models.User.objects.get(user_id=user_id)
        walls = user_and_map.walls
        return False
    except ObjectDoesNotExist:
        return True


def generate_map():
    """
    Generate map of size 20 x 20
    """
    walls = []
    enemies = []
    taken = []

    for i in range(24):
        x, y = generate_coordinate(taken, is_start=True)
        walls.append([x, y])
        taken.append([x, y])

    generate_enemy(taken, enemies, is_aggressive=True, count=3)
    generate_enemy(taken, enemies, is_aggressive=False, count=2)

    x, y = generate_coordinate(taken)
    stairs = [x, y]

    return walls, stairs, enemies


def generate_enemy(taken, enemies, is_aggressive=False, count=3):
    """
    Function for generating position of enemies
    """
    for i in range(count):
        x, y = generate_coordinate(taken)
        if is_aggressive:
            enemies.append(AggressiveEnemy(x, y))
        else:
            enemies.append(PassiveEnemy(x, y))
        taken.append([x, y])


def generate_coordinate(taken, is_start=False):
    """
    Function for generating coordinates
    """
    x = random.randint(1, 19)
    y = random.randint(1, 19)
    while is_start or ([x, y] in taken):
        x = random.randint(1, 19)
        y = random.randint(1, 19)
        is_start = False
    return x, y
