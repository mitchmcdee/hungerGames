#!/usr/bin/env python3
import socket
import select
import pygame
import random
from Player import Player
from Bullet import Bullet

class Server:
    WIDTH = 800
    HEIGHT = 600

    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.bullets = []
        self.players = {}
        self.playerClients = {}

    def send(self, client, message):
        try:
            response = client.send(bytes(message, encoding='utf-8'))
        except:
            return 'send', 'Failed to send message to client'

        return None, response

    def receive(self, client):
        try:
            response = client.recv(1024).decode('utf-8')
        except:
            return 'recv', 'Failed to read from client'

        if len(response) == 0:
            return 'closed', 'Client has closed'

        return None, response

    def addPlayer(self, client, name):
        randomColour = tuple([random.randrange(100, 255) for _ in range(3)])
        randomX = random.randrange(Server.WIDTH)
        randomY = random.randrange(Server.HEIGHT)

        self.players[client] = Player(name, 100, randomColour, randomX, randomY)
        self.playerClients[name] = client

    def getStateMessage(self):
        message = ('').join([player.state() for player in self.players.values()])
        message += ('').join([bullet.state() for bullet in self.bullets])
        return message

    def removeClient(self, client):
        client.close()
        self.clients.remove(client)
        print('Client disconnected')
        
        if client in self.players:
            player = self.players[client]
            del self.players[client]
            del self.playerClients[player.name]
            print('{0} disconnected'.format(player.name))

    def readFromClients(self, clientList):
        for client in clientList:
            err, response = self.receive(client)

            try:
                client.getpeername()
            except:
                self.removeClient(client)
                continue

            if err == 'closed':
                self.removeClient(client)
                continue

            if err == 'recv':
                continue

            if client not in self.players:
                name = response
                if name in self.playerClients:
                    print('Someone tried to join with a non-unique user name')
                    self.send(client, 'Error: User name already taken')
                    continue

                print('{0} has joined'.format(name))
                self.addPlayer(client, name)
                continue

            r = response.split(';')
            if len(r) < 2:
                continue

            p = r[-1] # Player (if any)
            b = r[-2] # Bullet (if any)
            if len(p) == 0 or p[0] != '|' or p[-1] != '|':
                continue

            p = p.strip('|').split(':')
            if len(p) != 5:
                continue

            name, hp, colourValues, x, y  = p
            p = self.players[client]
            p.x = int(x)
            p.y = int(y)

            if len(b) == 0 or b[0] != '(' or b[-1] != ')':
                continue

            b = b[1:-1].replace(' ','').split(',')
            if len(b) != 5:
                continue

            uid = int(b[0])
            owner = b[1].strip('\'')
            x = int(b[2])
            y = int(b[3])
            angle = float(b[4])

            self.bullets.append(Bullet(uid, owner, x, y, angle))

    def writeToClients(self, clientList):
        [self.send(client, self.getStateMessage()) for client in clientList]

    def getClients(self):
        connections, _, _ = select.select([self.server], [], [], 0.015)

        for connection in connections:
            client, _ = connection.accept()
            self.clients.append(client)

        try:
            readList, writeList, _ = select.select(self.clients, self.clients, [], 0.015)
        except:
            return [], []

        return readList, writeList
            
    def tickBullets(self):
        [bullet.tick() for bullet in self.bullets]

    def checkCollisions(self):
        deadBullets = []

        for bullet in self.bullets:
            if bullet.x < 0 or bullet.y < 0 or bullet.x > Server.WIDTH or bullet.y > Server.HEIGHT:
                deadBullets.append(bullet)
                continue

            for player in self.players.values():
                if bullet.owner == player.name:
                    continue

                if not bullet.getRect().colliderect(player.getRect()):
                    continue
                
                player.damage(9)
                deadBullets.append(bullet)

        [self.bullets.remove(bullet) for bullet in deadBullets]

    def run(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('', 40000))
        self.server.listen()
        print('Server started on port ' + str(self.server.getsockname()[1]))

        while True:
            readList, writeList = self.getClients()
            self.readFromClients(readList)
            self.writeToClients(writeList)
            self.tickBullets()
            self.checkCollisions()

        self.server.close()

if __name__ == '__main__':
    Server().run()