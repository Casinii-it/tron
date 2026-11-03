import numpy as np
import pygame
from pygame import Rect, Color, Event
import math
import time
import sys
np.set_printoptions(threshold=sys.maxsize)

class Game:
    def __init__(self):
        self.game_started = False

    def new_game(self):
        self.game_started = True
        self.game_over = False

        self.trail_board = np.zeros((104,80))
        self.player_board = np.zeros((104,80))
        self.player_board[84, 40] = 1
        self.player_board[19, 40] = 2

        self.player1_direction = np.array([-1, 0], dtype=int)
        self.player1_position = np.array([84, 40])
        self.player1_alive = True

        self.player2_direction = np.array([1, 0], dtype=int)
        self.player2_position = np.array([19, 40])
        self.player2_alive = True

    @staticmethod
    def out_of_bounds(array: np.ndarray):
        if array[0] < 0 or array[1] < 0 or array[0] > 103 or array[1] > 79:
            return True
        else:
            return False


    def input_to_array(self, input: Event):
        p1_dir = np.zeros(2, dtype=int)
        p2_dir = np.zeros(2, dtype=int)
    
        match input.key:
            case pygame.K_w:
                p2_dir[1] = 1
            case pygame.K_s:
                p2_dir[1] = -1
            case pygame.K_d:
                p2_dir[0] = 1
            case pygame.K_a:
                p2_dir[0] = -1

            case pygame.K_UP:
                p1_dir[1] = 1
            case pygame.K_DOWN:
                p1_dir[1] = -1
            case pygame.K_RIGHT:
                p1_dir[0] = 1
            case pygame.K_LEFT:
                p1_dir[0] = -1

        return p1_dir, p2_dir

    def game_step(self, p1_input: np.ndarray, p2_input: np.ndarray):
        if not self.game_started:
            raise RuntimeError("Start the game with `new_game()` first!")


        if p1_input.any() and (p1_input + self.player1_direction).any():
            self.player1_direction = p1_input
        if p2_input.any() and (p2_input + self.player2_direction).any():
            self.player2_direction = p2_input


        p1_newpos = self.player1_position + self.player1_direction

        if self.out_of_bounds(p1_newpos): 
            self.player1_alive = False
        elif self.trail_board[tuple(p1_newpos)].any() or self.player_board[tuple(p1_newpos)] == 2:
            self.player1_alive = False
        else:
            self.trail_board[tuple(self.player1_position)] = 1
            self.player_board[tuple(self.player1_position)] = 0
            self.player_board[tuple(p1_newpos)] = 1
            self.player1_position = p1_newpos


        p2_newpos = self.player2_position + self.player2_direction

        if self.out_of_bounds(p2_newpos): 
            self.player2_alive = False
        elif self.trail_board[tuple(p2_newpos)].any() or self.player_board[tuple(p2_newpos)] == 1:
            self.player2_alive = False
        else:
            self.trail_board[tuple(self.player2_position)] = 2
            self.player_board[tuple(self.player2_position)] = 0
            self.player_board[tuple(p2_newpos)] = 2
            self.player2_position = p2_newpos


        if not self.player1_alive or not self.player2_alive:
            self.game_over = True

            if self.player1_alive and not self.player2_alive:
                self.winner = 1

            if not self.player1_alive and self.player2_alive:
                self.winner = 2

            if not self.player1_alive and not self.player2_alive:
                self.winner = 0
            print(self.winner)


og_w = 104
og_h = 80
mult = 8

WIDTH = og_w * mult
HEIGHT = og_h * mult

SPEED = 30
ACCURACY = 2

game = Game()
game.new_game()


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True
p1_input = np.zeros(2)
p2_input = np.zeros(2)

frame = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            p1_input, p2_input = game.input_to_array(event)

    frame += 1

    if frame % (60/SPEED*ACCURACY) == 0:

        game.game_step(p1_input, p2_input)
        screen.fill("black")
        for x in range(og_w):
            for y in range(og_h):
                new_y = og_h-y

                if game.trail_board[x,y] == 1:
                    pygame.draw.rect(screen, Color(75,75,255), Rect(x*mult, new_y*mult, mult, mult))

                if game.trail_board[x,y] == 2:
                    pygame.draw.rect(screen, Color(255,75,75), Rect(x*mult, new_y*mult, mult, mult))

                if game.player_board[x,y] == 1:
                    pygame.draw.rect(screen, Color(0,0,255), Rect(x*mult, new_y*mult, mult, mult))

                if game.player_board[x,y] == 2:
                    pygame.draw.rect(screen, Color(255,0,0), Rect(x*mult, new_y*mult, mult, mult))

        if game.game_over:
            time.sleep(1)
            pygame.quit()
            sys.exit()


    pygame.display.flip()
    #print(clock.get_fps())
    clock.tick(60 * ACCURACY)  
pygame.quit()