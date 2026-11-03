import numpy as np

class game:
    def new_game():
        board = np.zeros((80,104), device=bool)
        print(board)