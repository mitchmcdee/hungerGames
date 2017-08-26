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
                    print('Someone tried to join with a non-unique user name')
                    self.send(client, 'Error: User name already taken')
                    continue

                print('{0} has joined'.format(response))
                self.addPlayer(client, response)
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