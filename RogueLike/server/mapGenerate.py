import random

from server.characters import AggressiveEnemy, Player, CharacterEncoder, PassiveEnemy

SIZE_OF_MAP = 19
COUNT_OF_WALLS = 24

def generate_map():
    """
    Generate map of size 20 x 20
    """
    walls = []
    enemies = []
    taken = []

    for i in range(COUNT_OF_WALLS):
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
    x = random.randint(1, SIZE_OF_MAP)
    y = random.randint(1, SIZE_OF_MAP)
    while is_start or ([x, y] in taken):
        x = random.randint(1, SIZE_OF_MAP)
        y = random.randint(1, SIZE_OF_MAP)
        is_start = False
    return x, y
