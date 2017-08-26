#!/usr/bin/env python3
import socket
import select
import pygame
import random
from Player import Player

class Server:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.players = {}
        self.playerClients = {}

    def send(self, server, message):
        try:
            server.send(bytes(message, encoding='utf-8'))
        except:
            return 'send', 'Failed to send {0} to {1}'.format(message, server)

        return None, None

    def receive(self, server):
        try:
            response = server.recv(4096).decode('utf-8')
        except:
            return 'recv', 'Failed to receive from {0}'.format(server)

        if len(response) == 0:
            return 'closed', '{0} has closed'.format(server)

        return None, response

    def addPlayer(self, client, name):
        randomColour = tuple([random.randrange(100, 255) for _ in range(3)])
        randomX = random.randrange(800)
        randomY = random.randrange(600)
        self.players[client] = Player(name, randomColour, randomX, randomY)
        self.playerClients[name] = client

    def getStateMessage(self):
        return ('').join([player.state() for player in self.players.values()])

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
                if response in self.playerClients:
                    print('{0} tried to join with a non-unique user name'.format(client))
                    self.send(client, 'Error: User name already taken')
                    continue

                print('{0} has joined'.format(response))
                self.addPlayer(client, response)
                self.send(client, 'Welcome ' + response)
                continue

            p = response.split(';')[-1]

            if p[0] != '|' or p[-1] != '|':
                continue

            p = p.strip('|').split(':')
            if len(p) != 4:
                continue

            name, colourValues, x, y  = p
            p = self.players[client]
            p.x = int(x)
            p.y = int(y)

    def writeToClients(self, clientList):
        for client in clientList:
            self.send(client, self.getStateMessage())

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
            
    def run(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('', 40000))
        self.server.listen()
        print('Server started on port ' + str(self.server.getsockname()[1]))

        while True:
            readList, writeList = self.getClients()
            self.readFromClients(readList)
            self.writeToClients(writeList)

        self.server.close()

if __name__ == '__main__':
    Server().run()