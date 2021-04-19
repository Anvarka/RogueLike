import json
import random
from rest_framework.decorators import api_view
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from enum import Enum
from server import models
from ast import literal_eval


class Move(Enum):
    up = "up"
    down = "down"
    left = "left"
    right = "right"


class UserEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, models.User):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


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
        "player": user_info.player
    }
    return JsonResponse(response_message, safe=False)


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
    cur_x = player[0]
    cur_y = player[1]

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
    walls = literal_eval(user_info.walls)
    stairs = user_info.stairs

    if x > 19 or y > 19 or x < 0 or y < 0 or (new_pos in walls):
        new_pos = [cur_x, cur_y]

    if new_pos == stairs:
        walls, stairs = generate_map()
        user_info.walls = walls
        user_info.stairs = stairs
        new_pos = [0, 0]

    user_info.player = new_pos
    response_message = {
        "walls": user_info.walls,
        "player": user_info.player
    }
    user_info.save()

    return JsonResponse(response_message, safe=False)


@api_view(['POST'])
def connect(request):
    """
    Connect with server
    Register of user
    """
    request_message = json.loads(request.body)
    user_id = request_message["user_id"]

    if is_user_new(user_id):
        print(user_id)
        walls, stairs = generate_map()
        print("dffsf")
        models.User.objects.create(user_id=user_id, walls=walls, stairs=stairs, player=[0, 0])
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
    is_start = True
    x = -1
    y = -1
    for i in range(16):
        while is_start or ([x, y] in walls):
            x = random.randint(1, 19)
            y = random.randint(1, 19)
            is_start = False
        walls.append([x, y])

    while [x, y] in walls:
        x = random.randint(1, 19)
        y = random.randint(1, 19)
    stairs = [x, y]
    return f"{walls}", stairs
