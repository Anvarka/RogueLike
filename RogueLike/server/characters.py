import random
from abc import ABC, abstractmethod
from typing import Any
import json


class MoveStrategy(ABC):
    @staticmethod
    @abstractmethod
    def get_next_move(cur_pos, level):
        pass


class RandomMoveStrategy(MoveStrategy):
    @staticmethod
    def get_next_move(cur_pos, level):
        return random.choice(['up', 'down', 'left', 'right'])


class AggressiveMoveStrategy(MoveStrategy):
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
    def should_attack(self, x, y, level):
        pass

    @abstractmethod
    def can_move(self, x, y, level):
        pass

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

        if self.should_attack(cur_x, cur_y, level):
            # insert attack here
            pass

        return


class NPC(Character):
    @abstractmethod
    def get_next_move(self, level):
        pass


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

    def can_move(self, x, y, level):
        if x < 0 or y < 0 or x > 19 or y > 19:
            return False
        if [x, y] in level.walls:
            return False
        if [x, y] in [e.cur_pos for e in level.enemies]:
            return False
        if [x, y] == level.player.cur_pos:
            return False
        return True

    def should_attack(self, x, y, level):
        return [x, y] == level.player

    def player_visible(self, level):
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

    def should_attack(self, x, y, level):
        return [x, y] in level.enemies

    def can_move(self, x, y, level):
        if x < 0 or y < 0 or x > 19 or y > 19:
            return False
        if [x, y] in level.walls:
            return False
        if [x, y] in [e.cur_pos for e in level.enemies]:
            return False
        return True

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
        if isinstance(o, AggressiveEnemy):
            return {'kind': 'agr_enemy', 'cur_pos': o.cur_pos, 'health': o.health}
        if isinstance(o, Player):
            return {'kind': 'player', 'cur_pos': o.cur_pos, 'health': o.health}
        return super().default(o)


class CharacterDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super(CharacterDecoder, self).__init__(object_hook=CharacterDecoder.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(obj):
        if (ch_type := obj.get('kind', '')) == 'agr_enemy':
            return AggressiveEnemy(obj['cur_pos'][0], obj['cur_pos'][1], obj['health'])
        elif ch_type == 'player':
            return Player(obj['cur_pos'][0], obj['cur_pos'][1], obj['health'])
        return obj
