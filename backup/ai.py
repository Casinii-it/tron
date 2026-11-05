import torch
from torch import nn
import random
import math
import signal
import numpy as np



class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(16645, 1024),
            nn.ReLU(),
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Linear(1024, 4),
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
        np.array(player).flatten()
    ))
    
    return flattened_gamestate



def get_ai_move(flattened_gamestate, model, raw=False):
    model.eval()

    move_scores = model(torch.tensor(flattened_gamestate, dtype=torch.float32))

    move_list = move_scores.tolist()
    max_index = move_list.index(max(move_list))

    array_index = math.floor(max_index/2)
    array_value = 2 * ((max_index + 1) % 2) - 1

    array = np.zeros(2, dtype=int)
    array[array_index] = array_value
    
    if raw:
        return array, move_scores
        
    else:
        return array
    

if __name__ == "__main__":    
    from tron_game import Game
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

    optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    #optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)



    WIDTH = 104
    HEIGHT = 80
    counter = 0
    print("Loop started")
    while not STOP:
        game = Game()
        game.new_game(WIDTH, HEIGHT)
        
        positions = []
        running = True
        outcome = 0
        while running:
            flattened_gamestate = get_flattened_gamestate(game, 2)
            
            if random.random() < 0.2:
                random_int = random.randint(0,3)
                array_index = math.floor(random_int/2)
                array_value = 2 * ((random_int + 1) % 2) - 1

                p1_input = np.zeros(2, dtype=int)
                p1_input[array_index] = array_value
                p1_raw = torch.zeros(4)
                p1_raw[random_int] = 1
            else:
                p1_input, p1_raw = get_ai_move(get_flattened_gamestate(game, 1), model, raw=True)


            if random.random() < 0.2:
                random_int = random.randint(0,3)
                array_index = math.floor(random_int/2)
                array_value = 2 * ((random_int + 1) % 2) - 1

                p2_input = np.zeros(2, dtype=int)
                p2_input[array_index] = array_value
                p2_raw = torch.zeros(4)
                p2_raw[random_int] = 1
            else:
                p2_input, p2_raw = get_ai_move( get_flattened_gamestate(game, 2), model, raw=True)


            positions.append([[get_flattened_gamestate(game, 1), get_flattened_gamestate(game, 2)], [p1_raw.tolist(), p2_raw.tolist()]])

            game.game_step(p1_input, p2_input, WIDTH, HEIGHT)

            if game.game_over: 
                print("GAME END")
                running = False


        
        turns = 0
        model.train()
        criterion = nn.MSELoss()
        for idx, state in enumerate(positions):
            turns += 1
            for player, raw in enumerate(state[1]):

                match game.winner:
                    case 0: expected = .5
                    case 1: 
                        if player == 0: expected = 1
                        else: expected = 0
                    case 2:
                        if player == 0: expected = 0
                        else: expected = 1


                prediction = model(torch.tensor(state[0][player], dtype=torch.float32))
                actual = prediction.detach().clone()
                actual[raw.index(max(raw))] = expected

                optimizer.zero_grad()
                
                
                
                loss = criterion(prediction, actual)
                #print(raw)
                loss *= math.tanh((0.95**(((len(positions)-idx)/3))*(100/len(positions)) + 1.4))
                
                if turns == 1:
                    print(loss)
                    print(len(positions), "\n\n")
                
                #loss = torch.tensor(w_or_l*5 - 2, dtype=torch.float32)
                loss.backward() 
                optimizer.step()
        
        counter +=1
            

    torch.save(model.state_dict(), "tron_model.pth")
    print("Model saved.")