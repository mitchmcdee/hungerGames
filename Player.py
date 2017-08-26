#!/usr/bin/env python3
import pygame

class Player:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y

    def state(self):
        return f'{self.name},{self.x},{self.y}'