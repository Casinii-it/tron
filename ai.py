import torch
from torch import nn
from tron_game import Game
import random
import math
import signal
import numpy as np


class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(16644, 1024),
            nn.ReLU(),
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Linear(1024, 4),
            nn.ReLU(),
            nn.Tanh()
        )

    def forward(self, x):
        logit = self.linear_relu_stack(x)
        return logit

def get_flattened_gamestate(game: Game, player):
    trail_board = game.trail_board
    player_board = game.player_board
    p1_dir = game.player1_direction
    p2_dir = game.player2_direction

    flattened_gamestate = np.concatenate((
        trail_board.flatten(),
        player_board.flatten(),
        p1_dir.flatten(),
        p2_dir.flatten(),
        player
    ))
    print(flattened_gamestate)
    return flattened_gamestate



def get_ai_move(flattened_gamestate, model):
    model.eval()

    move_scores = model(torch.tensor(flattened_gamestate, dtype=torch.float32))

    move_list = move_scores.tolist()
    max_index = move_list.index(max(move_list))

    array_index = math.floor(max_index/2)
    array_value = 2 * ((max_index + 1) % 2) - 1

    array = np.zeros(2)
    array[array_index] = array_value

    return array
    

if __name__ == "__main__":    
    device = "cpu"
    wins = 0
    draws = 0
    losses = 0

    STOP = False

    def handler(sig, frame):
        global STOP
        STOP = True

    signal.signal(signal.SIGINT, handler)
    model = NeuralNetwork().to(device)
    try:
        model.load_state_dict(torch.load("tron_model.pth", map_location=device))
        bad = False
        for name, p in model.named_parameters():
            if not torch.isfinite(p).all():
                print("NaN/Inf in parameter:", name)
                bad = True
                break
        print("model params finite?" , not bad)

    except Exception as e:
        print(e)

    #optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)



    WIDTH = 104
    HEIGHT = 80
    counter = 0
    print("Loop started")
    while not STOP:
        game = Game()
        game.new_game(WIDTH, HEIGHT)
        
        positions = []
        while 1:
            if game.game_over: 
                print("GAME END")
                break

            flattened_gamestate = get_flattened_gamestate(game, 1)
            positions.append(flattened_gamestate)

            p1_input = get_ai_move(flattened_gamestate, model)
            p2_input = get_ai_move(get_flattened_gamestate(game, 2), model)
            
            game.game_step(p1_input, p2_input, WIDTH, HEIGHT)


            turns = 0
            model.train()
            for state in positions:
                turns += 1

                state_tensor = torch.tensor(state, dtype=torch.float32)
                target = torch.tensor(w_or_l, dtype=torch.float32)

                optimizer.zero_grad()

                output = model(state_tensor).squeeze(-1)
                loss = (output - target)**2

                
                #loss = torch.tensor(w_or_l*5 - 2, dtype=torch.float32)
                loss.backward()
                optimizer.step()
            counter +=1
            

    torch.save(model.state_dict(), "tron_model.pth")
    print("Model saved.")