import json
import requests
import threading
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from concurrent.futures import ThreadPoolExecutor

from server import models
from server.characters import Player, CharacterEncoder
from server.mapGenerate import generate_map
from server.utils import create_response_message, get_user_url, create_new_level_map, \
    initialize_pos_new_player, session_exists, random_string

SIZE_OF_MAP = 19
COUNT_OF_WALLS = 24

is_make_move = False
is_last_player = False
active_user = None

turn_taken = threading.Condition()

current_players = {}  # user_id -> ip user
current_map = None


class PlayerNotifier:
    def __init__(self):
        self.last_notified = -1
        self.tp = ThreadPoolExecutor(1)

    def notify_next(self):
        self.tp.submit(self.notifiy_active_next)

    def get_user_num(self, id):
        """
        Function for getting user's number
        """
        for i, u in enumerate(current_players):
            if u == id:
                return i

    def notifiy_active_next(self):
        """
        Function that gives the user a certain amount of time to go
        """
        while True:
            if len(current_players) == 0:
                return

            global is_last_player, active_user, is_make_move
            self.last_notified = (self.last_notified + 1) % len(current_players)
            if self.last_notified == len(current_players) - 1:
                is_last_player = True
            notify_id = list(current_players.keys())[self.last_notified]
            active_user = notify_id

            print("NOTIFY ACTIVE: " + notify_id)
            req = requests.post(current_players[notify_id] + '/state', params={'value': 'ACTIVE'})
            is_make_move = False
            with turn_taken:
                print("START WAITING FOR MOVE")
                if turn_taken.wait_for(lambda: is_make_move, 10.0):
                    print("GOT MOVE IN TIME")
                    return
                else:
                    print("TRY TO NOTIFY NEXT")
                    for user_id_cur, ip_address in current_players.items():
                        requests.post(ip_address + '/state', params={'value': 'WAIT'})
                    continue


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
    with turn_taken:
        is_make_move = True
        turn_taken.notify()

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

    player_obj = models.User.objects.get(user_id=user_id)
    player_obj.last_map = user_info.map_id
    player_obj.player = player
    player_obj.save()
    response_message = create_response_message(user_info)
    user_info.save()

    requests.post(current_players[user_id] + '/state', params={'value': 'WAIT', 'map': 'map'})
    for user_id_cur, ip_address in current_players.items():
        requests.post(ip_address + '/map')

    notifier.notify_next()
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
        player = Player(0, 0, user_id)
        map_id = random_string()
        models.Session.objects.create(map_id=map_id,
                                      walls=walls,
                                      stairs=stairs,
                                      players=[player],
                                      enemies=enemies,
                                      game_over=False)
        user = models.User.objects.create(user_id=user_id, player=player, last_map=map_id)
        user.save()
    else:
        session = models.Session.objects.get()
        try:
            old_user = models.User.objects.get(user_id=user_id)
            if old_user.last_map == session.map_id:
                session.players.append(old_user.player)
            else:
                player = initialize_pos_new_player(session, user_id)
                old_user.player = player
                old_user.last_map = session.map_id
                old_user.save()
        except ObjectDoesNotExist:
            player = initialize_pos_new_player(session, user_id)
            user = models.User.objects.create(user_id=user_id, player=player, last_map=session.map_id)
            user.save()
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
    """
    If the user wants to quit the game. We save where it was saved,
    but remove it from the current map.
    """
    request_message = json.loads(request.body)
    user_id = request_message["user_id"]
    print("DISCONNECT: " + user_id)
    user_num = notifier.get_user_num(user_id)
    if user_num <= notifier.last_notified:
        notifier.last_notified -= 1
    current_players.pop(user_id)
    if active_user == user_id:
        notifier.notify_next()
    user_info = models.Session.objects.get()
    user_info.players = list(filter(lambda u: u.user_id != user_id, user_info.players))
    user_info.save()
    print("DISCONNECTED: " + user_id)
    return HttpResponse("Disconnected")
