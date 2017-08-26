#!/usr/bin/env python3
import socket
import select
import random
import pygame
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
            return 'send', f'Failed to send {message} to {server}'

        return None, None

    def receive(self, server):
        try:
            response = self.server.recv(1024).decode('utf-8')
        except:
            return 'recv', f'Failed to receive from {server}'

        if len(response) == 0:
            return 'closed', f'{server} has closed'

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

    def parseResponse(self, response):
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
                self.players[name] = Player(name, colour, int(x), int(y))
            else:
                p = self.players[name]
                p.x = int(x)
                p.y = int(y)

            seenPlayers.add(name)

        deadPlayers = list(self.players.keys() - seenPlayers)
        for name in deadPlayers:
            del self.players[name]

    def drawPlayers(self):
        for player in self.players.values():
            pygame.draw.circle(self.screen, player.colour, (player.x, player.y), 10)

    def handleInput(self):
        if self.name not in self.players:
            return

        p = self.players[self.name]

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

    def sendState(self):
        if self.name not in self.players:
            return
        
        self.send(self.server, self.players[self.name].state())

    def run(self, ip, port):
        self.connect(ip, port)
        
        while self.running:
            self.screen.fill((0,0,0))
            err, response = self.receive(self.server)
            if err == 'closed' or err == 'taken':
                self.quit(response)

            if err == 'recv':
                continue

            self.parseResponse(response)
            self.handleInput()
            self.drawPlayers()
            self.sendState()
            pygame.display.flip()

        quit('Shutting down')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: ./Client.py `name`')
        sys.exit(0)

    Client(sys.argv[1]).run('13.236.0.194', 40000)