#!/usr/bin/env python3
import socket
import random
import pygame
import pygame.gfxdraw
import sys
from Player import Player
from Bullet import Bullet

class Client:
    WIDTH = 800
    HEIGHT = 600

    def __init__(self, name):
        self.name = name
        self.screen = pygame.display.set_mode((Client.WIDTH, Client.HEIGHT))
        self.running = True
        self.players = {}
        self.bullets = []
        self.bulletFired = False

    def send(self, server, message):
        try:
            response = self.server.send(bytes(message, encoding='utf-8'))
        except:
            return 'send', 'Failed to send message to server'

        return None, response

    def receive(self, server):
        try:
            response = self.server.recv(1024).decode('utf-8')
        except:
            return 'recv', 'Failed to read from server'

        if response[:5] == 'Error':
            return 'taken', 'Username has already been taken'

        return None, response

    def quit(self, reason):
        print(reason)
        self.server.close()
        sys.exit(0)

    def connect(self, ip, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((ip, port))
        self.server.setblocking(False)
        self.send(self.server, self.name)
        err, response = self.receive(self.server)

        if err == 'taken':
            self.quit(response)

    def getState(self):
        err, response = self.receive(self.server)
        if err == 'taken':
            self.quit(response)

        if err == 'recv':
            return

        seenPlayers = set()
        self.bullets = []
        for response in response.split(';'):
            if len(response) < 7:
                continue

            if response[0] == '/' and response[-1] == '/':

                b = response.strip('/').split(':')
                if len(b) != 4:
                    continue

                name, x, y, angle  = b
                if len(name) == 0 or len(x) == 0 or len(y) == 0:
                    continue

                print('added bullet!')
                x = int(x)
                y = int(y)
                angle = int(angle)

                self.bullets.append(Bullet(name, x, y, angle))
                continue

            # Check if start and stop chars exist
            if response[0] != '|' or response[-1] != '|':
                continue

            p = response.strip('|').split(':')
            if len(p) != 5:
                continue

            name, hp, colourValues, x, y  = p
            if len(name) == 0 or len(hp) == 0 or len(colourValues) < 7 or len(x) == 0 or len(y) == 0:
                continue

            hp = int(hp)
            x = int(x)
            y = int(y)

            if name not in self.players:
                colourValues = colourValues[1:-1].split(',')
                colour = tuple([int(x.strip()) for x in colourValues])
                self.players[name] = Player(name, hp, colour, x, y)
            
            elif name != self.name:
                p = self.players[name]
                p.x = x
                p.y = y

            self.players[name].hp = hp
            seenPlayers.add(name)

        self.removeOldPlayers(seenPlayers)

    def checkAlive(self):
        if self.players[self.name].hp <= 0:
            self.quit('You died! Rejoin the server to resume playing')

    def removeOldPlayers(self, seenPlayers):
        if len(seenPlayers) == 0:
            return

        deadPlayers = list(self.players.keys() - seenPlayers)
        for name in deadPlayers:
            del self.players[name]

    def drawPlayers(self):
        self.screen.fill((0,0,0))

        font = pygame.font.SysFont("arial", 12)
        for p in self.players.values():
            pygame.gfxdraw.filled_circle(self.screen, p.x, p.y, Player.WIDTH, p.colour)
            pygame.gfxdraw.aacircle(self.screen, p.x, p.y, Player.WIDTH, (255,255,255))

            healthWidth = int(Player.WIDTH * 2 * p.hp / 100.0)
            healthHeight = 5
            healthPoints = [(p.x - Player.WIDTH, p.y - Player.WIDTH * 2), (p.x - Player.WIDTH, p.y - Player.WIDTH * 2 + healthHeight),
                            (p.x - Player.WIDTH + healthWidth, p.y - Player.WIDTH * 2 + healthHeight), (p.x - Player.WIDTH + healthWidth, p.y - Player.WIDTH * 2)]

            pygame.gfxdraw.filled_polygon(self.screen, healthPoints, (0,200,0))
            pygame.gfxdraw.aapolygon(self.screen, healthPoints, (255,255,255))

            label = font.render(p.name.upper(), 1, (255,255,0))
            w,h = pygame.Surface.get_size(label)
            self.screen.blit(label, (p.x - w // 2, p.y - int(Player.WIDTH * 5 / 2) - h // 2))

            pygame.display.update(p.getRect())

    def drawBullets(self):
        for b in self.bullets:
            pygame.gfxdraw.filled_circle(self.screen, b.x, b.y, Bullet.WIDTH, (255,255,255))
            pygame.display.update(b.getRect())


    def handleInput(self):
        if self.name not in self.players:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.bulletFired = True

        p = self.players[self.name]

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            p.y -= 4
        if keys[pygame.K_DOWN]:
            p.y += 4
        if keys[pygame.K_RIGHT]:
            p.x += 4
        if keys[pygame.K_LEFT]:
            p.x -= 4

        halfWidth = Player.WIDTH // 2
        p.x = max(min(p.x, Client.WIDTH - halfWidth), halfWidth)
        p.y = max(min(p.y, Client.HEIGHT - halfWidth), halfWidth)

    def getBullet(self):
        if not self.bulletFired:
            return ''

        self.bulletFired = False

        p = self.players[self.name]
        x,y = pygame.mouse.get_pos()

        return str((self.name,p.x,p.y,x,y))

    def sendState(self):
        if self.name not in self.players:
            return
        
        self.send(self.server, ';' + self.getBullet() + self.players[self.name].state())

    def run(self, ip, port):
        self.connect(ip, port)
        pygame.init()
        
        while self.running:
            self.getState()
            self.checkAlive()
            self.handleInput()
            self.sendState()
            self.drawPlayers()
            self.drawBullets()

        quit('Shutting down')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: ./Client.py `name`')
        sys.exit(0)

    Client(sys.argv[1]).run('13.236.0.194', 40000)