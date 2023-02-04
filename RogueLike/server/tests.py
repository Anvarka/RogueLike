"""
Please, turn on 1) the server + 2) client "was" + 3) client "user"(for test_multiplayer)
for the tests to work correctly
"""
import json

from django.test import TestCase, Client
from server import models
from server.mapGenerate import generate_map
from server.utils import is_user_new, check_position

URL = "http://127.0.0.1:8000/server/"
CONNECT = "connect/"
CORRECT_DISCONNECT = "correct_disconnect/"
MAP = "map/"
MOVE = "move/"


class RogueLikeTestCase(TestCase):

    def test_overlapping_generate_map(self):
        """
        Checking the correctness of the generate map function
        """
        for i in range(10_000):
            walls, stairs, enemies = generate_map()
            self.assertFalse(any(enemy in walls for enemy in stairs))
            self.assertFalse(any(enemy in stairs for enemy in enemies))
            self.assertFalse(any(enemy in walls for enemy in enemies))

    def setUp(self):
        """
        Create a client that will simulate a user
        """
        self.client = Client(HTTP_HOST='localhost:8000')

    def test_connect_disconnect(self):
        """
        Check the connection to the server
        """
        status_content = self.connection(user_id="was")
        self.assertEqual(status_content, "Поздравляю, вы зарегистрированы, was")
        self.assertFalse(is_user_new("was"))

        status_disconnect = self.connection(user_id="was", disconnect=True)
        self.assertEqual(status_disconnect, "Disconnected")

        decode_info = self.post_to_map(user_id="was")
        data = json.loads(decode_info)

        # remember the user although he was removed from the players
        self.assertEqual(data['players'], [])
        self.assertFalse(is_user_new("was"))

    def test_get_map_and_move(self):
        """
        Check to get map and move in map
        """
        self.connection(user_id="was")
        content_info = self.post_to_map(user_id="was")
        data = json.loads(content_info)

        self.assertEqual(len(data["walls"]), 24)
        self.assertEqual(len(data["enemies"]), 5)
        self.assertEqual(data["players"],
                         [{'x': 0, 'y': 0, 'health': 100, 'kind': 'player', 'user_id': 'was'}])

        self.make_move("was", direction="right")
        self.connection("was", disconnect=True)

        user_info = models.User.objects.get(user_id="was")
        correct_pos = [1, 0] if check_position([1, 0]) else [0, 0]
        self.assertEqual(user_info.player.cur_pos, correct_pos)

    def test_multiplayers(self):
        """
        Function for testing of multiplayer's properties
        """
        self.connection(user_id="was")
        self.connection(user_id="user")

        content_info = self.post_to_map(user_id="was")
        data = json.loads(content_info)
        self.assertEqual(len(data["players"]), 2)

        self.assertEqual([data["players"][0]["x"], data["players"][0]["y"]], [0, 0])
        self.assertEqual([data["players"][1]["x"], data["players"][1]["y"]], [0, 1])

        self.make_move("was", direction="right")
        self.connection("was", disconnect=True)

        self.make_move("user", direction="right")
        self.connection("user", disconnect=True)

        user_info = models.User.objects.get(user_id="was")
        correct_pos = [1, 0] if check_position([1, 0]) else [0, 0]
        self.assertEqual(user_info.player.cur_pos, correct_pos)

        user_info = models.User.objects.get(user_id="user")
        correct_pos = [1, 1] if check_position([1, 1]) else [0, 1]
        self.assertEqual(user_info.player.cur_pos, correct_pos)

    def connection(self, user_id, disconnect=False):
        """
        Function, for to connect|disconnect with server
        """
        request_user_id = {
            "user_id": user_id
        }
        if disconnect:
            response_status = self.client.post(URL + CORRECT_DISCONNECT, json.dumps(request_user_id),
                                               content_type="application/json")
        else:
            response_status = self.client.post(URL + CONNECT, json.dumps(request_user_id),
                                               content_type="application/json")
        return response_status.content.decode('UTF-8')

    def post_to_map(self, user_id):
        """
        Function for getting map
        """
        request_user_id = {
            "user_id": user_id
        }
        response_info = self.client.post(URL + MAP, json.dumps(request_user_id),
                                         content_type="application/json")

        return response_info.content.decode("UTF-8").replace("'", '"')

    def make_move(self, user_id, direction):
        """
        Function for moving of player
        """
        request_move = {
            "user_id": user_id,
            "direction": direction
        }
        return self.client.post(URL + MOVE, json.dumps(request_move), content_type="application/json")
