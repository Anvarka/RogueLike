import asyncio
import json
import time
import requests
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse

from server import models
from server.characters import AggressiveEnemy, Player, CharacterEncoder, PassiveEnemy
from server.mapGenerate import generate_map
from server.utils import create_response_message, get_user_url, create_new_level_map, \
    initialize_pos_new_player, session_exists

SIZE_OF_MAP = 19
COUNT_OF_WALLS = 24

is_make_move = False
is_last_player = False
active_user = None

current_players = {}  # user_id -> ip user
current_map = None


class PlayerNotifier:
    def __init__(self):
        self.last_notified = -1

    def notifiy_active_next(self):
        global is_last_player, active_user, is_make_move
        self.last_notified = (self.last_notified + 1) % len(current_players)
        if self.last_notified == len(current_players) - 1:
            is_last_player = True
        notify_id = list(current_players.keys())[self.last_notified]
        active_user = notify_id

        print("NOTIFY ACTIVE: " + notify_id)
        req = requests.post(current_players[notify_id] + '/state', params={'value': 'ACTIVE'})
        print(req.url)
        t = 10
        # is_make_move = False
        while t:
            time.sleep(1)
            t -= 1
            if is_make_move:
                is_make_move = False
                return
        is_make_move = False
        time.sleep(1)
        req = requests.post(current_players[notify_id] + '/state', params={'value': 'WAIT'})
        print(req.url)
        self.notifiy_active_next()


notifier = PlayerNotifier()


@api_view(['POST'])
def get_map(request):
    """
    Function for getting map
    """
    if not session_exists():
        return HttpResponse("Вы еще не зарегистрированы")

    user_info = models.Session.objects.get()
    response_message = create_response_message(user_info)

    return JsonResponse(response_message, encoder=CharacterEncoder, safe=False)


@api_view(['POST'])
def player_move(request):
    """
    Change the position of the player depending on the command
    """
    global is_make_move, is_last_player
    is_make_move = True

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
        create_new_level_map(user_info)

    if is_last_player:
        for enemy in user_info.enemies:
            enemy.move(enemy.get_next_move(user_info), user_info)
        is_last_player = False

    response_message = create_response_message(user_info)
    user_info.save()

    requests.post(current_players[user_id] + '/state', params={'value': 'WAIT', 'map': 'map'})
    for user_id_cur, ip_address in current_players.items():
        requests.post(ip_address + '/map')

    notifier.notifiy_active_next()
    return JsonResponse(response_message, encoder=CharacterEncoder, safe=False)


@api_view(['POST'])
def connect(request):
    """
    Connect with server and register of user
    """
    global active_user

    request_message = json.loads(request.body)
    user_id = request_message["user_id"]

    user_url = get_user_url(request, user_id)
    current_players[user_id] = user_url
    print("USER_URL: " + user_url)

    if not session_exists():
        walls, stairs, enemies = generate_map()
        models.Session.objects.create(walls=walls,
                                      stairs=stairs,
                                      players=[Player(0, 0, user_id)],
                                      enemies=enemies,
                                      game_over=False)
    else:
        session = models.Session.objects.get()
        if user_id not in [pl.user_id for pl in session.players]:
            initialize_pos_new_player(session, user_id)
        session.save()

    response = HttpResponse(f"Поздравляю, вы зарегистрированы, {user_id}")
    print(current_players)
    if len(current_players) == 1 or active_user not in current_players:
        init_state = 'ACTIVE'
        active_user = user_id
    else:
        init_state = 'WAIT'
    requests.post(user_url + '/state', params={'value': init_state})

    for user_id_cur, ip_address in current_players.items():
        requests.post(ip_address + '/map')

    return response


@api_view(['POST'])
def correct_disconnect(request):
    request_message = json.loads(request.body)
    user_id = request_message["user_id"]
    if active_user == user_id:
        requests.post(current_players[user_id] + '/state', params={'value': 'WAIT'})
        notifier.notifiy_active_next()
    current_players.pop(user_id)
    user_info = models.Session.objects.get()
    user_info.players.remove(user_id)
    user_info.save()
    # Убрать из карты
    # Убрать из текущих игроков
    # Но запомнить место на карте / здоровье ...
    # И возмжно поменять last_modified

#
# def incorrect_disconnect(request):
#     request_message = json.loads(request.body)
#     user_id = request_message["user_id"]
#     current_players.pop(user_id)
#     # Убрать из карты
#     # Убрать из текущих игроков
#     # Но запомнить место на карте / здоровье ...
#     # И возмжно поменять last_modified
