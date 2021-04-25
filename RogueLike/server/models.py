from django.db import models

from server.characters import CharacterEncoder, CharacterDecoder


def get_fresh_default():
    return []


class User(models.Model):
    user_id = models.CharField(max_length=100)
    walls = models.JSONField(default=get_fresh_default)
    stairs = models.JSONField(default=get_fresh_default)
    player = models.JSONField(default=get_fresh_default, encoder=CharacterEncoder, decoder=CharacterDecoder)
    enemies = models.JSONField(default=get_fresh_default, encoder=CharacterEncoder, decoder=CharacterDecoder)

    def __str__(self):
        return f"user_id: {self.user_id}, walls: {self.walls}, player: {self.player}, enemies: {self.enemies}"
