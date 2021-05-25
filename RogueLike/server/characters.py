import random
from abc import ABC, abstractmethod
from typing import Any
from server.constants import LEVEL_MIN_X, LEVEL_MIN_Y, LEVEL_MAX_X, LEVEL_MAX_Y
import json


def plot_line(x0, y0, x1, y1):
    line = []
    dx =  abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else - 1
    err = dx + dy  # error value e_xy
    while True:
        line.append([x0, y0])
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy: # e_xy+e_x > 0
            err += dy
            x0 += sx
        if e2 <= dx:  # e_xy+e_y < 0
            err += dx
            y0 += sy
    return line


class MoveStrategy(ABC):
    """
    Class describing the behavior of character
    """

    @staticmethod
    @abstractmethod
    def get_next_move(cur_pos, level):
        pass


class RandomMoveStrategy(MoveStrategy):
    """
    Class describing the behavior of an passive character
    """

    @staticmethod
    def get_next_move(cur_pos, level):
        return random.choice(['up', 'down', 'left', 'right'])


class AggressiveMoveStrategy(MoveStrategy):
    """
    Сlass describing the behavior of an aggressive character
    """

    @staticmethod
    def get_next_move(cur_pos, level):
        possible_directions = []
        if cur_pos[0] < level.player.cur_pos[0]:  # X coordinate
            possible_directions.append('right')
        elif cur_pos[0] > level.player.cur_pos[0]:
            possible_directions.append('left')
        if cur_pos[1] < level.player.cur_pos[1]:  # Y coordinate
            possible_directions.append('down')
        elif cur_pos[1] > level.player.cur_pos[1]:
            possible_directions.append('up')
        if not possible_directions:
            return RandomMoveStrategy.get_next_move(cur_pos, level)
        return random.choice(possible_directions)


class Character(ABC):
    """
    Class describing the character
    """

    @property
    @abstractmethod
    def cur_pos(self):
        pass

    @cur_pos.setter
    @abstractmethod
    def cur_pos(self, value):
        pass

    @property
    @abstractmethod
    def health(self):
        pass

    @health.setter
    @abstractmethod
    def health(self, value):
        pass

    @property
    @abstractmethod
    def attack(self):
        pass

    @attack.setter
    @abstractmethod
    def attack(self, value):
        pass

    @abstractmethod
    def should_attack(self, opposing_char):
        pass

    def can_move(self, x, y, level):
        if x < LEVEL_MIN_X or y < LEVEL_MIN_Y or x > LEVEL_MAX_X or y > LEVEL_MAX_Y:
            return False
        if [x, y] in level.walls:
            return False
        if [x, y] in [e.cur_pos for e in level.enemies]:
            return False
        if [x, y] == level.player.cur_pos:
            return False
        return True

    @abstractmethod
    def encode_for_client(self):
        pass

    def move(self, direction, level):
        cur_x, cur_y = self.cur_pos
        if direction == 'up':
            cur_y -= 1
        elif direction == 'down':
            cur_y += 1
        elif direction == 'left':
            cur_x -= 1
        elif direction == 'right':
            cur_x += 1
        else:
            raise ValueError('unknown direction')

        if self.can_move(cur_x, cur_y, level):
            self.cur_pos = [cur_x, cur_y]
            return

        if (opposing_char := level.get_char_at(cur_x, cur_y)) is not None:
            if self.should_attack(opposing_char):
                opposing_char.health = opposing_char.health - self.attack
                if opposing_char.health <= 0:
                    level.remove_char(opposing_char)
                    self.cur_pos = [cur_x, cur_y]
        return


class NPC(Character):
    @abstractmethod
    def get_next_move(self, level):
        pass


class PassiveEnemy(NPC):
    """
    Class of a passive enemy
    """

    def __init__(self, x, y, health=10):
        self.x = x
        self.y = y
        self.health = health
        self.attack = 3

    @property
    def cur_pos(self):
        """
        return the current position of enemy
        """
        return [self.x, self.y]

    @cur_pos.setter
    def cur_pos(self, value):
        """
        setter the current position of enemy
        """
        self.x, self.y = value

    def get_next_move(self, level):
        """
        return the next position if enemy
        """
        return RandomMoveStrategy.get_next_move(self.cur_pos, level)

    def should_attack(self, opposing_char):
        """
        don't attack enemy
        """
        return isinstance(opposing_char, Player)

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        self._health = value

    @property
    def attack(self):
        return self._attack

    @attack.setter
    def attack(self, value):
        self._attack = value

    def encode_for_client(self):
        return self.cur_pos


class AggressiveEnemy(NPC):
    def __init__(self, x, y, health=20):
        self.x = x
        self.y = y
        self.health = health
        self.attack = 5

    @property
    def cur_pos(self):
        return [self.x, self.y]

    @cur_pos.setter
    def cur_pos(self, value):
        self.x, self.y = value

    def get_next_move(self, level):
        if self.player_visible(level):
            return AggressiveMoveStrategy.get_next_move(self.cur_pos, level)
        return RandomMoveStrategy.get_next_move(self.cur_pos, level)

    def should_attack(self, opposing_char):
        return isinstance(opposing_char, Player)

    def player_visible(self, level):
        line = plot_line(*self.cur_pos, *level.player.cur_pos)
        if self.cur_pos == line[-1]:
            line = reversed(line)
        for (i, cell) in enumerate(line):
            if i >= 5:
                return False
            if cell in level.walls:
                return False
        return True

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        self._health = value

    @property
    def attack(self):
        return self._attack

    @attack.setter
    def attack(self, value):
        self._attack = value

    def encode_for_client(self):
        return self.cur_pos


class Player(Character):
    """
    Class describing the player
    """

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.attack = 10

    @property
    def cur_pos(self):
        return [self.x, self.y]

    @property
    def health(self):
        return self._health

    @property
    def attack(self):
        return self._attack

    def should_attack(self, opposing_char):
        return isinstance(opposing_char, AggressiveEnemy) or isinstance(opposing_char, PassiveEnemy)

    @health.setter
    def health(self, value):
        self._health = value

    @attack.setter
    def attack(self, value):
        self._attack = value

    @cur_pos.setter
    def cur_pos(self, value):
        self.x, self.y = value

    def encode_for_client(self):
        return self.cur_pos


class CharacterEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Character):
            encoded = {'x': o.x, 'y': o.y, 'health': o.health}
            if isinstance(o, AggressiveEnemy):
                encoded['kind'] = 'agr_enemy'
            elif isinstance(o, PassiveEnemy):
                encoded['kind'] = 'passive_enemy'
            else:
                encoded['kind'] = 'player'
            return encoded
        return super().default(o)


class CharacterDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super(CharacterDecoder, self).__init__(object_hook=CharacterDecoder.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(obj):
        if (ch_type := obj.get('kind', '')) == 'agr_enemy':
            return AggressiveEnemy(obj['x'], obj['y'], obj['health'])
        elif (ch_type := obj.get('kind', '')) == 'passive_enemy':
            return PassiveEnemy(obj['x'], obj['y'], obj['health'])
        elif ch_type == 'player':
            return Player(obj['x'], obj['y'], obj['health'])
        return obj
