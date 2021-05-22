from django.urls import path

from server import views

urlpatterns = [
    path('map/', views.get_map, name='map'),
    path('move/', views.player_move, name='move'),
    path('connect/', views.connect, name='connect'),
    path('correct_disconnect/', views.correct_disconnect, name='correct_disconnect')
]

current_players = []
