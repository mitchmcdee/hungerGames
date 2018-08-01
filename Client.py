#!/usr/bin/env python3
import socket
import random
import pygame
import pygame.gfxdraw
import sys
from math import atan2
from Player import Player
from Bullet import Bullet

def angleBetween(p1, p2):
    return atan2(p2[1]-p1[1], p2[0]-p1[0])

class Client:
    WIDTH = 1280
    HEIGHT = 720

    def __init__(self, name):
        self.name = name
        self.screen = pygame.display.set_mode((Client.WIDTH, Client.HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE)
        self.running = True
        self.players = {}
        self.bullets = {}
        self.bulletCount = 0
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
        
        while True:
            err, response = self.receive(self.server)

            if err == 'taken':
                self.quit(response)

            if err != 'recv':
                break

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
                angle = float(angle)


                if name == self.name and uid not in self.bullets:
                    self.bulletCount += 1

                self.bullets[uid] = (name, x, y)
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
            if self.bullets[uid][0] == self.name:
                self.bulletCount -= 1

            del self.bullets[uid]

    def removeOldPlayers(self, seenPlayers):
        if len(seenPlayers) == 0:
            return

        deadPlayers = list(self.players.keys() - seenPlayers)
        for name in deadPlayers:
            del self.players[name]

    def drawSprites(self):
        s = pygame.Surface((Bullet.WIDTH, Bullet.WIDTH))
        pygame.draw.circle(s, (255,255,255), (Bullet.WIDTH // 2, Bullet.WIDTH // 2), Bullet.WIDTH // 2)
        for name,x,y in self.bullets.values():
            self.screen.blit(s, (x,y))

        font = pygame.font.SysFont("arial", 15)
        for p in self.players.values():
            pygame.gfxdraw.filled_circle(self.screen, p.x, p.y, Player.WIDTH // 2, (255,255,255))
            pygame.gfxdraw.filled_circle(self.screen, p.x, p.y, int(Player.WIDTH / 2.4), p.colour)
            pygame.gfxdraw.aacircle(self.screen, p.x, p.y, Player.WIDTH // 2, (255,255,255))

            healthWidth = int(Player.WIDTH * 2 * p.hp / 100.0)
            healthHeight = 5
            healthPadding = 23
            healthPoints = [(p.x - Player.WIDTH, p.y - healthPadding), (p.x - Player.WIDTH, p.y + healthHeight - healthPadding),
                            (p.x - Player.WIDTH + healthWidth, p.y + healthHeight - healthPadding), (p.x - Player.WIDTH + healthWidth, p.y - healthPadding)]

            pygame.gfxdraw.filled_polygon(self.screen, healthPoints, (0,200,0))
            pygame.gfxdraw.aapolygon(self.screen, healthPoints, (255,255,255))

            label = font.render(p.name.upper(), True, (255,255,0))
            w,h = pygame.Surface.get_size(label)
            self.screen.blit(label, (p.x - w // 2, p.y - Player.WIDTH - h // 2))

    def handleInput(self):
        if self.name not in self.players:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
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

        if self.bulletCount >= Bullet.MAX_BULLETS:
            return ''

        p = self.players[self.name]
        x,y = pygame.mouse.get_pos()
        angle = angleBetween((p.x, p.y), (x,y))

        return str((random.randrange(sys.maxsize),self.name,p.x,p.y,angle))

    def sendState(self):
        if self.name not in self.players:
            return
        
        self.send(self.server, ';' + self.getBullet() + self.players[self.name].state())

    def run(self, ip, port):
        self.connect(ip, port)
        pygame.init()
        background = pygame.Surface(self.screen.get_size())
        background.fill((0,0,0))
        background = background.convert()

        clock = pygame.time.Clock()
        
        while self.running:
            self.screen.blit(background, (0,0))

            self.getState()
            self.checkAlive()
            self.handleInput()
            self.sendState()
            self.drawSprites()

            pygame.display.update()

            clock.tick(60)
            print(clock.get_fps())

        quit('Shutting down')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: ./Client.py `name`')
        sys.exit(0)

    Client(sys.argv[1]).run('52.65.5.173', 12345)