#!/usr/bin/env python3
import pygame

class Player:
    def __init__(self, name, colour, x, y):
        self.name = name
        self.colour = colour
        self.x = x
        self.y = y

    def state(self):
        return '{0}:{1}:{2}:{3}'.format(self.name, self.colour, self.x, self.y)