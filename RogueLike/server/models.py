from django.db import models

from server.characters import CharacterEncoder, CharacterDecoder


def get_fresh_default():
    return []


def get_fresh_false():
    return False


class Session(models.Model):
    map_id = models.CharField(max_length=100, default="")
    walls = models.JSONField(default=get_fresh_default)
    stairs = models.JSONField(default=get_fresh_default)
    players = models.JSONField(default=get_fresh_default, encoder=CharacterEncoder, decoder=CharacterDecoder)
    enemies = models.JSONField(default=get_fresh_default, encoder=CharacterEncoder, decoder=CharacterDecoder)
    game_over = models.JSONField(default=get_fresh_false)

    def get_char_at(self, x, y):
        for pl in self.players:
            if [x, y] == pl.cur_pos:
                return pl
        for en in self.enemies:
            if [x, y] == en.cur_pos:
                return en
        return None

    def remove_char(self, char):
        if char in self.players:
            self.players.remove(char)
            return
        # Else char is enemy
        self.enemies.remove(char)

# TODO: rename to session?
class User(models.Model):
    user_id = models.CharField(max_length=100, default="")
    last_map = models.CharField(max_length=100, default="")
    player = models.JSONField(default=get_fresh_default, encoder=CharacterEncoder, decoder=CharacterDecoder)

