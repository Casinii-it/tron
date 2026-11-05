import torch
from torch import nn
import random
import math
import signal
import numpy as np
import torch.nn.functional as F


class NeuralNetwork(nn.Module):
    def __init__(self):
        super(NeuralNetwork, self).__init__()
        self.conv1 = nn.Conv2d(5, 16, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)

        self.conv3 = nn.Conv2d(32, 48, 3, padding=1)

        self.fc1 = nn.Linear(48 * 10 * 13, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 3)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = torch.flatten(x, start_dim=1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x))
        x = F.normalize(x)
        return x

def prepare_model_input(game: Game, player):
    trail_board = game.trail_board
    player_board = game.player_board


    match player:
        case 1: direction = game.player1_direction
        case 2: direction = game.player2_direction

    model_input = np.squeeze(np.stack((
        trail_board,
        player_board,
        torch.zeros(104,80).fill_(player),
        torch.zeros(104,80).fill_(direction[0]),
        torch.zeros(104,80).fill_(direction[1])
    )))
    
    return model_input



def get_ai_move(model_input, model, game: Game, player: int, raw=False):
    model.eval()

    move_scores = model(torch.tensor(model_input, dtype=torch.float32).unsqueeze(0))
    move_list = move_scores.squeeze().tolist()
    
    max_index = move_list.index(max(move_list))

    if player == 1:
        current_dir = game.player1_direction
    else:
        current_dir = game.player2_direction

    match max_index:
        case 0: array = np.zeros(2, dtype=int)
        case 1: array = np.array([-current_dir[1], current_dir[0]])
        case 2: array = np.array([current_dir[1], -current_dir[0]])

    if raw:
        return array, move_scores.squeeze().tolist()
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

    optimizer = torch.optim.SGD(model.parameters(), lr=0.03, momentum=0.9)
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
        counter += 1
        while running:
            model_input = prepare_model_input(game, 2)
            
            if random.random() < 0:#.15:
                random_int = random.randint(0,2)
                p1_raw = [0,0,0]
                p1_raw[random_int] = 1

                match random_int:
                    case 0: p1_input = np.zeros(2, dtype=int)
                    case 1: p1_input = np.array([-game.player1_direction[1], game.player1_direction[0]])
                    case 2: p1_input = np.array([game.player1_direction[1], -game.player1_direction[0]])
            else:
                p1_input, p1_raw = get_ai_move(prepare_model_input(game, 1), model, game, 1, raw=True)


            if random.random() < 0:#.15:
                random_int = random.randint(0,2)
                p2_raw = [0,0,0]
                p2_raw[random_int] = 1

                match random_int:
                    case 0: p2_input = np.zeros(2, dtype=int)
                    case 1: p2_input = np.array([-game.player2_direction[1], game.player2_direction[0]])
                    case 2: p2_input = np.array([game.player2_direction[1], -game.player2_direction[0]])
            else:
                p2_input, p2_raw = get_ai_move(prepare_model_input(game, 2), model, game, 2, raw=True)


            positions.append([[prepare_model_input(game, 1), prepare_model_input(game, 2)], [p1_raw, p2_raw]])

            game.game_step(p1_input, p2_input, WIDTH, HEIGHT)

            if game.game_over: 
                print("GAME END")
                print(len(positions))
                print()
                running = False


        
        turns = 0
        model.train()   
        criterion = nn.MSELoss()
        optimizer.zero_grad()
        total_loss = 0
        if len(positions) < 0:
            continue

        for idx, state in enumerate(positions):
            turns += 1
            for player, raw in enumerate(state[1]):



                
                survival = idx/len(positions)


                if len(positions) < 10:
                    expected = 0
                else:
                    match game.winner:
                        case 0: expected = .2
                        case 1:
                            if player == 0: expected = 1
                            else: expected = 0
                        case 2:
                            if player == 0: expected = 0
                            else: expected = 1


                



                prediction = model(torch.tensor(state[0][player], dtype=torch.float32).unsqueeze(0)).squeeze()
                actual = prediction.detach().clone() #torch.zeros(3) 
                #for i in range(3):
                #    actual[i] = 0
                
                actual[raw.index(max(raw))] = expected
                print(actual)

                
                
                
                loss = criterion(prediction, actual)

                if len(positions) < 50:
                    length_mod = -1
                else:
                    length_mod = 0

                if game.winner == 0:
                    reward = .5 + 0.2*survival + length_mod*.5
                elif game.winner == player +1:
                    reward = 1 + survival
                else:
                    reward = -.5 + length_mod


                total_loss += loss
                #print(raw)
                #loss *= math.tanh((0.95**(((len(positions)-idx)/3))*(100/len(positions)) + 1.4))
                
                    
                
                #loss = torch.tensor(w_or_l*5 - 2, dtype=torch.float32)
        
        if total_loss != 0:
            print(len(positions), "\n\n")
            total_loss /= len(positions) * 2
            total_loss.backward() 
            
            print(total_loss)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
        
        counter +=1
        if counter % 100 == 0:
            torch.save(model.state_dict(), "tron_model.pth")
            

    torch.save(model.state_dict(), "tron_model.pth")
    print("Model saved.")