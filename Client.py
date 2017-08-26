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
        self.players = {}

    def send(self, server, message):
        err = None
        response = None
        _, writeList, _ = select.select([], [self.server], [], 0.05)

        if len(writeList) == 0:
            return 'empty', None

        try:
            self.server.send(bytes(message, encoding='utf-8'))
        except:
            err = 'send'
            response = f'Failed to send {message} to {server}'

        return err, response

    def receive(self, server):
        err = None
        response = None
        readList, _, _ = select.select([self.server], [], [], 0.05)

        if len(readList) == 0:
            return 'empty', None

        try:
            response = self.server.recv(1024).decode('utf-8')
        except:
            err = 'recv'
            response = f'Failed to receive from {server}'

        return err, response

    def randomColour(self):
        return tuple([random.randrange(255) for _ in range(3)])

    def quit(self, reason):
        print(reason)
        self.server.close()
        sys.exit(0)

    def connect(self, ip, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((ip, port))
        self.send(self.server, self.name)
        err, response = self.receive(self.server)
        if err:
            self.quit(response)

    def parseResponse(self, response):
        if response[:5] == 'Error':
            self.quit(response)

        players = response.split(';')
        for player in players:
            p = player.split(',')

            if len(p) > 3:
                continue

            name, x, y  = p
            if name not in self.players:
                self.players[name] = Player(name, int(x), int(y))

    def drawPlayers(self):
        for player in self.players.values():
            print(f'drawing {player.name}')
            pygame.draw.circle(self.screen, self.randomColour(), (player.x, player.y), 10)

    def run(self, ip, port):
        self.connect(ip, port)
        
        running = True
        while running:
            err, response = self.receive(self.server)
            if err:
                self.quit(response)

            if len(response) == 0:
                continue

            self.parseResponse(response)
            self.drawPlayers()
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

        self.server.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('usage: python3 Client.py `name` `ip:port`')
        sys.exit(0)

    name = sys.argv[1]
    ip, port = sys.argv[2].split(':')

    Client(name).run(ip, int(port))