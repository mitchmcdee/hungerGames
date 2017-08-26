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
            return 'send', f'Failed to send {message} to {server}'

        return None, None

    def receive(self, server):
        try:
            response = server.recv(1024).decode('utf-8')
        except:
            return 'recv', f'Failed to receive from {server}'

        if len(response) == 0:
            return 'closed', f'{server} has closed'

        return None, response

    def addPlayer(self, client, name):
        randomColour = tuple([random.randrange(255) for _ in range(3)])
        randomX = random.randrange(800)
        randomY = random.randrange(600)
        self.players[client] = Player(name, randomColour, randomX, randomY)
        self.playerClients[name] = client

    def getStateMessage(self):
        return (';').join([player.state() for player in self.players.values()])

    def removeClient(self, client):
        client.close()
        self.clients.remove(client)

        if client not in self.players:
            print(f'Removed client: {client}')
            return

        player = self.players[client]
        del self.players[client]
        del self.playerClients[player.name]
        print(f'Removed client: {client} and player: {player.name}')

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
                    print(f'{client} tried to join with a non-unique user name')
                    self.send(client, 'Error: User name already taken')
                    continue

                print(f'{client} has joined as {response}')
                self.addPlayer(client, response)
                self.send(client, 'Welcome ' + response)
                continue

            p = response.split(':')

            if len(p) != 4:
                continue

            name, colourValues, x, y  = p
            p = self.players[client]
            p.x = int(x)
            p.y = int(y)

    def writeToClients(self, clientList):
        for client in clientList:
            self.send(client, self.getStateMessage())

    def process(self):
        connections, _, _ = select.select([self.server], [], [], 0.05)

        for connection in connections:
            client, _ = connection.accept()
            self.clients.append(client)

        try:
            readList, writeList, _ = select.select(self.clients, self.clients, [], 0.05)
        except:
            return

        self.readFromClients(readList)
        self.writeToClients(writeList)
            
    def run(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('', 40000))
        self.server.listen()
        print('Running on port ' + str(self.server.getsockname()[1]))

        while True:
            self.process()

        self.server.close()

if __name__ == '__main__':
    Server().run()