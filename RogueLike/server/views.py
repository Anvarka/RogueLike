import json
import random
from rest_framework.decorators import api_view
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from enum import Enum
from server import models
from server.characters import AggressiveEnemy, Player, CharacterEncoder

from server.characters import PassiveEnemy


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
    if is_user_new(request_message["user_id"]):
        return HttpResponse("Вы еще не зарегистрированы")
    user_id = request_message["user_id"]
    user_info = models.User.objects.get(user_id=user_id)
    response_message = {
        "walls": user_info.walls,
        "stairs": user_info.stairs,
        "player": user_info.player,
        "enemies": user_info.enemies,
        "game_over": False
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
    user_info = models.User.objects.get(user_id=user_id)
    player = user_info.player
    cur_x = player.cur_pos[0]
    cur_y = player.cur_pos[1]

    if direction == Move.up.name:
        new_pos = [cur_x, cur_y - 1]
    elif direction == Move.down.name:
        new_pos = [cur_x, cur_y + 1]
    elif direction == Move.left.name:
        new_pos = [cur_x - 1, cur_y]
    elif direction == Move.right.name:
        new_pos = [cur_x + 1, cur_y]
    else:
        return HttpResponse("Error")
    x = new_pos[0]
    y = new_pos[1]
    walls = user_info.walls
    stairs = user_info.stairs

    if x > 19 or y > 19 or x < 0 or y < 0 or (new_pos in walls):
        new_pos = [cur_x, cur_y]

    if new_pos == stairs:
        walls, stairs, enemies = generate_map()
        user_info.walls = walls
        user_info.stairs = stairs
        user_info.enemies = enemies

        new_pos = [0, 0]

    user_info.player.cur_pos = new_pos
    for enemy in user_info.enemies:
        enemy.move(enemy.get_next_move(user_info), user_info)

    response_message = {
        "walls": user_info.walls,
        "player": user_info.player,
        "stairs": user_info.stairs,
        "enemies": user_info.enemies,
        "game_over": False
    }
    user_info.save()

    return JsonResponse(response_message, encoder=CharacterEncoder, safe=False)


@api_view(['POST'])
def connect(request):
    """
    Connect with server
    Register of user
    """
    request_message = json.loads(request.body)
    user_id = request_message["user_id"]

    if is_user_new(user_id):
        walls, stairs, enemies = generate_map()
        models.User.objects.create(user_id=user_id,
                                   walls=walls,
                                   stairs=stairs,
                                   player=Player(0, 0),
                                   enemies=enemies,
                                   game_over=False)
        return HttpResponse(f"Поздравляю, вы зарегистрированы, {user_id}")
    else:
        return HttpResponse(f"Вы уже были зарегистрированы, {user_id}")


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
