from tron_game import Game
import numpy as np





WIDTH = 104
HEIGHT = 80

game = Game()
game.new_game(WIDTH, HEIGHT)

while 1:
    game.game_step(p1_input, p2_input, WIDTH, HEIGHT)
    if game.game_over:
        