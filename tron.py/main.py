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

    def new_game(self, w, h):
        self.game_started = True
        self.game_over = False

        self.trail_board = np.zeros((w,h))
        self.player_board = np.zeros((w,h))
        self.player_board[84, 40] = 1
        self.player_board[19, 40] = 2

        self.player1_direction = np.array([-1, 0], dtype=int)
        self.player1_position = np.array([84, 40])
        self.player1_alive = True

        self.player2_direction = np.array([1, 0], dtype=int)
        self.player2_position = np.array([19, 40])
        self.player2_alive = True

    @staticmethod
    def out_of_bounds(array: np.ndarray, w, h):
        if array[0] < 0 or array[1] < 0 or array[0] > w-1 or array[1] > h-1:
            return True
        else:
            return False


    def input_to_array(self, input: Event, player_1: bool):
        array = np.zeros(2, dtype=int)

        if player_1:
            match input.key:
                case pygame.K_UP:
                    array[1] = 1
                case pygame.K_DOWN:
                    array[1] = -1
                case pygame.K_RIGHT:
                    array[0] = 1
                case pygame.K_LEFT:
                    array[0] = -1

        else:
            match input.key:
                case pygame.K_w:
                    array[1] = 1
                case pygame.K_s:
                    array[1] = -1
                case pygame.K_d:
                    array[0] = 1
                case pygame.K_a:
                    array[0] = -1

        return array

    def game_step(self, p1_input: np.ndarray, p2_input: np.ndarray, w, h):
        if not self.game_started:
            raise RuntimeError("Start the game with `new_game()` first!")


        if p1_input.any() and (p1_input + self.player1_direction).any():
            self.player1_direction = p1_input
        if p2_input.any() and (p2_input + self.player2_direction).any():
            self.player2_direction = p2_input


        p1_newpos = self.player1_position + self.player1_direction

        if self.out_of_bounds(p1_newpos, w, h): 
            self.player1_alive = False
        elif self.trail_board[tuple(p1_newpos)].any() or self.player_board[tuple(p1_newpos)] == 2:
            self.player1_alive = False
        else:
            self.trail_board[tuple(self.player1_position)] = 1
            self.player_board[tuple(self.player1_position)] = 0
            self.player_board[tuple(p1_newpos)] = 1
            self.player1_position = p1_newpos


        p2_newpos = self.player2_position + self.player2_direction

        if self.out_of_bounds(p2_newpos, w, h): 
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


#og_w = 104
#og_h = 80

og_w = 104
og_h = 80

MULT = 10

WIDTH = og_w * MULT
HEIGHT = og_h * MULT

SPEED = 30
SCREEN_FPS = 60
BLINK_SPEED = 2

game = Game()
game.new_game(og_w, og_h)


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
            if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT, pygame.K_LEFT]:
                p1_input = game.input_to_array(event, True)
            elif event.key in [pygame.K_w, pygame.K_s, pygame.K_d, pygame.K_a]:
                p2_input = game.input_to_array(event, False)
            

    frame += 1

    if frame % (SCREEN_FPS/SPEED) == 0:

        game.game_step(p1_input, p2_input, og_w, og_h)
        screen.fill(20)
        for x in range(og_w):
            for y in range(og_h):
                new_y = og_h-y
                
                if game.trail_board[x,y] == 1:
                    pygame.draw.rect(screen, Color(75,75,255), Rect(x*MULT, new_y*MULT, MULT, MULT))

                if game.trail_board[x,y] == 2:
                    pygame.draw.rect(screen, Color(255,75,75), Rect(x*MULT, new_y*MULT, MULT, MULT))

                if game.player_board[x,y] == 1:
                    pygame.draw.rect(screen, Color(0,0,255), Rect(x*MULT, new_y*MULT, MULT, MULT))

                if game.player_board[x,y] == 2:
                    pygame.draw.rect(screen, Color(255,0,0), Rect(x*MULT, new_y*MULT, MULT, MULT))

        if game.game_over:
            #blink_period = SCREEN_FPS/BLINK_SPEED
            time.sleep(5)

            
            pygame.quit()
            sys.exit()


    pygame.display.flip()
    #print(clock.get_fps())
    clock.tick(SCREEN_FPS)  
pygame.quit()