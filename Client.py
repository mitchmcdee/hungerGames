#!/usr/bin/env python3
import socket
import random
import pygame
import pygame.gfxdraw
import sys
from math import atan2, degrees
from Player import Player
from Bullet import Bullet

def angleBetween(p1, p2):
    return int(degrees(atan2(p2[1]-p1[1], p2[0]-p1[0])))

class Client:
    WIDTH = 800
    HEIGHT = 600

    def __init__(self, name):
        self.name = name
        self.screen = pygame.display.set_mode((Client.WIDTH, Client.HEIGHT))
        self.running = True
        self.players = {}
        self.bullets = {}
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
        seenBullets = set()
        for response in response.split(';'):
            if len(response) < 7:
                continue

            if response[0] == '/' and response[-1] == '/':
                b = response.strip('/').split(':')
                if len(b) != 5:
                    continue

                uid, name, x, y, angle = b
                if len(uid) == 0 or len(name) == 0 or len(x) == 0 or len(y) == 0:
                    continue

                uid = int(uid)
                x = int(x)
                y = int(y)
                angle = int(angle)

                print('added bullet ', x, y, angle)

                self.bullets[uid] = Bullet(uid, name, x, y, angle)
                seenBullets.add(uid)
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

        self.removeOldBullets(seenBullets)
        self.removeOldPlayers(seenPlayers)

    def checkAlive(self):
        if self.name not in self.players:
            return

        if self.players[self.name].hp <= 0:
            self.quit('You died! Rejoin the server to resume playing')

    def removeOldBullets(self, seenBullets):
        if len(seenBullets) == 0:
            return

        deadBullets = list(self.bullets.keys() - seenBullets)
        for uid in deadBullets:
            del self.bullets[uid]

    def removeOldPlayers(self, seenPlayers):
        if len(seenPlayers) == 0:
            return

        deadPlayers = list(self.players.keys() - seenPlayers)
        for name in deadPlayers:
            del self.players[name]

    def drawSprites(self):
        for b in self.bullets.values():
            pygame.gfxdraw.filled_circle(self.screen, b.x, b.y, Bullet.WIDTH, (255,255,255))

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
        if keys[pygame.K_w]:
            p.y -= 4
        if keys[pygame.K_a]:
            p.x -= 4
        if keys[pygame.K_s]:
            p.y += 4
        if keys[pygame.K_d]:
            p.x += 4

        halfWidth = Player.WIDTH // 2
        p.x = max(min(p.x, Client.WIDTH - halfWidth), halfWidth)
        p.y = max(min(p.y, Client.HEIGHT - halfWidth), halfWidth)

    def getBullet(self):
        if not self.bulletFired:
            return ''

        self.bulletFired = False

        p = self.players[self.name]
        x,y = pygame.mouse.get_pos()
        angle = angleBetween((p.x, p.y), (x,y))

        print((p.x, p.y), (x, y), angle)
        return str((random.randrange(sys.maxsize),self.name,p.x,p.y,angle))

    def sendState(self):
        if self.name not in self.players:
            return
        
        self.send(self.server, ';' + self.getBullet() + self.players[self.name].state())

    def run(self, ip, port):
        self.connect(ip, port)
        pygame.init()
        
        while self.running:
            self.screen.fill((0,0,0))

            self.getState()
            self.checkAlive()
            self.handleInput()
            self.sendState()
            self.drawSprites()

            pygame.display.update()

        quit('Shutting down')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: ./Client.py `name`')
        sys.exit(0)

    Client(sys.argv[1]).run('13.236.0.194', 40000)