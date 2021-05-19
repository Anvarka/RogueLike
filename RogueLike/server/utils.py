from enum import Enum

import random
import string

from django.core.exceptions import ObjectDoesNotExist
from server.mapGenerate import generate_map
from server.characters import Player

from server import models

SIZE_OF_MAP = 19


class Move(Enum):
    """
    Enum of different movement
    """
    up = "up"
    down = "down"
    left = "left"
    right = "right"


def random_string():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))


def create_response_message(user_info):
    """
    Function, for creating response message from the database's info
    """
    response_message = {
        "walls": user_info.walls,
        "stairs": user_info.stairs,
        "players": user_info.players,
        "enemies": user_info.enemies,
        "game_over": user_info.game_over
    }
    return response_message


def get_user_url(request, user_id):
    """
    Function for getting server address of player
    """
    user_url = request.build_absolute_uri('/').strip('/').rsplit(':', 1)[0]
    if user_id == 'was':
        return user_url + ':1235'
    else:
        return user_url + ':1234'


def create_new_level_map(user_info):
    """
    Update map because we move to a new level
    """
    walls, stairs, enemies = generate_map()
    user_info.walls = walls
    user_info.stairs = stairs
    user_info.enemies = enemies
    user_info.map_id = random_string()
    for (i, pl) in enumerate(user_info.players):
        pl.cur_pos = [0, i]
        player = models.User.objects.get(user_id=pl.user_id)
        player.player.cur_pos = pl.cur_pos
        player.last_map = user_info.map_id
        player.save()
    


def initialize_pos_new_player(session, user_id):
    """
    Function, which gives the position to the new user
    """
    taken_poses = []
    for playerObj in session.players:
        taken_poses.append(playerObj.cur_pos)
    for enemyObj in session.enemies:
        taken_poses.append(enemyObj.cur_pos)

    for i in range(SIZE_OF_MAP):
        if [0, i] in taken_poses:
            continue
        else:
            player = Player(0, i, user_id)
            session.players.append(player)
            return player

def session_exists():
    """
    Check the existence of a running session
    """
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
