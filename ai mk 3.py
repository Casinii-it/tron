import gymnasium as gym
from gymnasium.utils.env_checker import check_env
import numpy as np
from typing import Optional
import tron_game
from copy import deepcopy
from stable_baselines3 import A2C
import sys
import pygame
from pygame import Color, Rect

class CustomEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, render_mode=None, width = 104, height = 80):
        self.width = width
        self.height = height
        
        pygame.init()
        self.MULT = 5
        self.screen = None

        self.render_mode = render_mode

        self.observation_space = gym.spaces.Dict(
            {
                "trail board": gym.spaces.Box(0, 3, shape=(width,height), dtype=int),
                "player board": gym.spaces.Box(0, 3, shape=(width,height), dtype=int),
                "player 1 dir": gym.spaces.Box(-1, 1, shape=(2,), dtype=int),
                "player 2 dir": gym.spaces.Box(-1, 1, shape=(2,), dtype=int),
                "player": gym.spaces.Discrete(3)
            }
        )

        self.action_space = gym.spaces.Discrete(4)

        self._action_to_direction = {
            0: np.array([0, 1]),
            1: np.array([-1, 0]),
            2: np.array([0, -1]),
            3: np.array([1, 0]),
        }

    def step(self, action):
        direction = self._action_to_direction[action]

        self.game = deepcopy(self.game)

        self.game.game_step(direction, np.zeros(2), self.width, self.height)

        terminated = self.game.game_over
        truncated = False
        reward = -10 if terminated else 0.01
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self.render()

        return observation, reward, terminated, truncated, info

    def reset(self, seed:Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)
        self.game = tron_game.Game()
        self.game.new_game(self.width, self.height, solo=True)

        observation = self._get_obs()
        info = self._get_info()


        return observation, info

    def render(self):
        game = self.game

        MULT = 5

        pygame.init()
        screen = pygame.display.set_mode((self.width * MULT, self.height* MULT))

        screen.fill(20)
        for x in range(self.width):
            for y in range(self.height):
                new_y = self.height-y-1
                
                if game.trail_board[x,y] == 1:
                    pygame.draw.rect(screen, Color(75,75,255), Rect(x*MULT, new_y*MULT, MULT, MULT))

                if game.trail_board[x,y] == 2:
                    pygame.draw.rect(screen, Color(255,75,75), Rect(x*MULT, new_y*MULT, MULT, MULT))

                if game.player_board[x,y] == 1:
                    pygame.draw.rect(screen, Color(0,0,255), Rect(x*MULT, new_y*MULT, MULT, MULT))

                if game.player_board[x,y] == 2:
                    pygame.draw.rect(screen, Color(255,0,0), Rect(x*MULT, new_y*MULT, MULT, MULT))
        
        pygame.display.flip()


    def close(self):        
        pygame.quit()

    def _get_obs(self, player:int=2):
        observations = {
            "trail board": self.game.trail_board,
            "player board": self.game.player_board,
            "player 1 dir": self.game.player1_direction,
            "player 2 dir": np.array([0,1]),#self.game.player2_direction,
            "player": player
        }
        return observations

    def _get_info(self):
        return {}

class CustomCNN

def action_to_direction(num: int):
    match num:
        case 0: return np.array([0, 1]),
        case 1: return np.array([-1, 0]),
        case 2: return np.array([0, -1]),
        case 3: return np.array([1, 0]),



from collections import defaultdict
import gymnasium as gym
import numpy as np


gym.register(
    id="gymnasium_env/Tron",
    entry_point=CustomEnv
)
env = gym.make("gymnasium_env/Tron")#, render_mode="human")


try:
    check_env(env)
    print("Environment passes all checks!")
except Exception as e:
    print(f"Environment has issues: {e}")
    sys.exit()


try:
    model = A2C.load("model.heehee", env)
    print("Model loaded successfully")
except:
    model = A2C("MultiInputPolicy", env, verbose=1)
    print("Model created successfully")

while 1:
    model.learn(total_timesteps=5_000, progress_bar=True)
    model.save("model.heehee")

vec_env = model.get_env()
obs = vec_env.reset()

game = tron_game.Game()
game.new_game(104,80)

while game.game_over:
    direction = action_to_direction(model.predict(obs, deterministic=True))

    
    # VecEnv resets automatically
    # if done:
    #   obs = vec_env.reset ()
    vec_env.render("human")
model.save("model.heehee")