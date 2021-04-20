from django.db import models


class User(models.Model):
    user_id = models.CharField(max_length=100)
    walls = models.JSONField(default=dict({'walls': []}))
    stairs = models.JSONField(default=dict({'stairs': []}))
    player = models.JSONField(default=dict({'player': []}))

    def __str__(self):
        return f"user_id: {self.user_id}, walls: {self.walls}, player: {self.player}"
