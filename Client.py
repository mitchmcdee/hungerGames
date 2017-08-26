#!/usr/bin/env python3
import socket
import random
import pygame
import pygame.gfxdraw
import sys
from Player import Player

class Client:
    def __init__(self, name):
        self.name = name
        self.screen = pygame.display.set_mode((800, 600))
        self.running = True
        self.players = {}

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
        players = response.split(';')
        for player in players:
            # Check minimum size is achieved, from |x,(x,x,x),x,x|
            if len(player) < 15:
                continue

            # Check if start and stop chars exist
            if player[0] != '|' or player[-1] != '|':
                continue

            p = player.strip('|').split(':')
            if len(p) != 4:
                continue

            name, colourValues, x, y  = p
            if len(name) == 0 or len(colourValues) < 7 or len(x) == 0 or len(y) == 0:
                continue

            x = int(x)
            y = int(y)

            if name not in self.players:
                colourValues = colourValues[1:-1].split(',')
                colour = tuple([int(x.strip()) for x in colourValues])
                self.players[name] = Player(name, colour, x, y)
            
            elif name != self.name:
                p = self.players[name]
                p.x = x
                p.y = y

            seenPlayers.add(name)

        self.removeOldPlayers(seenPlayers)

    def removeOldPlayers(self, seenPlayers):
        if len(seenPlayers) == 0:
            return

        deadPlayers = list(self.players.keys() - seenPlayers)
        for name in deadPlayers:
            del self.players[name]

    def getRect(self, p):
        width = Player.PLAYER_WIDTH
        return pygame.Rect(p.x - width // 2, p.y - width // 2, width, width)

    def drawPlayers(self):
        self.screen.fill((0,0,0))
        
        for p in self.players.values():
            pygame.gfxdraw.filled_circle(self.screen, p.x, p.y, Player.PLAYER_WIDTH, p.colour)
            pygame.gfxdraw.aacircle(self.screen, p.x, p.y, Player.PLAYER_WIDTH, (255,255,255))
            pygame.display.update(self.getRect(p))

    def handleInput(self):
        if self.name not in self.players:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

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

    def sendState(self):
        if self.name not in self.players:
            return
        
        self.send(self.server, self.players[self.name].state())

    def run(self, ip, port):
        self.connect(ip, port)
        
        while self.running:
            self.getState()
            self.handleInput()
            self.sendState()
            self.drawPlayers()

        quit('Shutting down')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: ./Client.py `name`')
        sys.exit(0)

    Client(sys.argv[1]).run('13.236.0.194', 40000)