#!/usr/bin/env python3
import pygame
from math import cos, sin

class Bullet:
    WIDTH = 5
    SPEED = 3.0

    def __init__(self, uid, owner, x, y, angle):
        print(x, y, angle)

        self.uid = uid
        self.owner = owner
        self.x = x
        self.y = y
        self.angle = angle

    def tick(self):
        print(self.angle)
        self.x += cos(self.angle) * Bullet.SPEED
        self.y += sin(self.angle) * Bullet.SPEED

    def getRect(self):
        return pygame.Rect(self.x - Bullet.WIDTH // 2, self.y - Bullet.WIDTH // 2, Bullet.WIDTH, Bullet.WIDTH)

    def state(self):
        return ';/{0}:{1}:{2}:{3}:{4}/'.format(self.uid, self.owner, int(self.x), int(self.y), self.angle)