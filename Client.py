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
            self.server.send(bytes(message, encoding='utf-8'))
        except:
            return 'send', 'Failed to send {0} to {1}'.format(message, server)

        return None, None

    def receive(self, server):
        try:
            response = self.server.recv(1024).decode('utf-8')
        except:
            return 'recv', 'Failed to receive from {0}'.format(server)

        if len(response) == 0:
            return 'closed', '{0} has closed'.format(server)

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
        self.send(self.server, self.name)
        err, response = self.receive(self.server)

        if err == 'taken' or err == 'recv':
            self.quit(response)

    def getState(self):
        err, response = self.receive(self.server)
        if err == 'closed' or err == 'taken':
            self.quit(response)

        if err == 'recv':
            return

        players = response.split(';')
        seenPlayers = set()
        for player in players:
            p = player.split(':')

            if len(p) != 4:
                continue

            name, colourValues, x, y  = p
            r, g, b = colourValues[1:-1].split(',')
            colour = (int(r.strip()), int(g.strip()), int(b.strip()))

            if name not in self.players:
                p = Player(name, colour, int(x), int(y))
                r = pygame.Rect(p.x - Player.PLAYER_WIDTH // 2, p.y - Player.PLAYER_WIDTH // 2, Player.PLAYER_WIDTH, Player.PLAYER_WIDTH)
                self.players[name] = (p, r)
            else:
                p,_ = self.players[name]
                p.x = int(x)
                p.y = int(y)
                r = pygame.Rect(p.x - Player.PLAYER_WIDTH // 2, p.y - Player.PLAYER_WIDTH // 2, Player.PLAYER_WIDTH, Player.PLAYER_WIDTH)
                self.players[name] = (p, r)

            seenPlayers.add(name)

        if len(seenPlayers) == 0:
            return

        deadPlayers = list(self.players.keys() - seenPlayers)
        for name in deadPlayers:
            del self.players[name]

    def drawPlayers(self):
        self.screen.fill((0,0,0))
        for player,r in self.players.values():
            pygame.gfxdraw.filled_circle(self.screen, player.x, player.y, Player.PLAYER_WIDTH, player.colour)
            pygame.gfxdraw.aacircle(self.screen, player.x, player.y, Player.PLAYER_WIDTH, (255,255,255))
            pygame.display.update(r)

    def handleInput(self):
        if self.name not in self.players:
            return

        p,r = self.players[self.name]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            p.y -= 10
        if keys[pygame.K_DOWN]:
            p.y += 10
        if keys[pygame.K_RIGHT]:
            p.x += 10
        if keys[pygame.K_LEFT]:
            p.x -= 10

        r = pygame.Rect(p.x - Player.PLAYER_WIDTH // 2, p.y - Player.PLAYER_WIDTH // 2, Player.PLAYER_WIDTH, Player.PLAYER_WIDTH)
        self.players[self.name] = (p, r)

    def sendState(self):
        if self.name not in self.players:
            return
        
        self.send(self.server, self.players[self.name][0].state())

    def run(self, ip, port):
        self.connect(ip, port)
        
        while self.running:
            self.getState()
            self.handleInput()
            self.drawPlayers()
            self.sendState()

        quit('Shutting down')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: ./Client.py `name`')
        sys.exit(0)

    Client(sys.argv[1]).run('13.236.0.194', 40000)