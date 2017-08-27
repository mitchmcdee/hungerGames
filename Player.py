#!/usr/bin/env python3
import pygame

class Player:
    WIDTH = 15

    def __init__(self, name, hp, colour, x, y):
        self.name = name
        self.hp = hp
        self.colour = colour
        self.x = x
        self.y = y

    def damage(self, damage):
        self.hp -= damage

    def getRect(self):
        return pygame.Rect(self.x - Player.WIDTH // 2, self.y - Player.WIDTH // 2, Player.WIDTH, Player.WIDTH)

    def state(self):
        return ';|{0}:{1}:{2}:{3}:{4}|'.format(self.name, self.hp, self.colour, self.x, self.y)