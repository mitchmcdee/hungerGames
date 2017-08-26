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
        self.playerNames = set()

    def send(self, server, message):
        err = None
        response = None
        _, writeList, _ = select.select([], [server], [], 0.05)

        if len(writeList) == 0:
            return 'empty', None

        try:
            server.send(bytes(message, encoding='utf-8'))
        except:
            err = 'send'
            response = f'Failed to send {message} to {server}'

        return err, response

    def receive(self, server):
        err = None
        response = None
        readList, _, _ = select.select([server], [], [], 0.05)

        if len(readList) == 0:
            return 'empty', None

        try:
            response = server.recv(1024).decode('utf-8')
        except:
            err = 'recv'
            response = f'Failed to receive from {server}'

        return err, response

    def addPlayer(self, client, name):
        randomX = random.randrange(800)
        randomY = random.randrange(600)
        self.players[client.getpeername()] = Player(name, randomX, randomY)
        self.playerNames.add(name)

    def getStateMessage(self):
        return (';').join([player.state() for player in self.players.values()])

    def removeClient(self, client):
        client.close()
        self.clients.remove(client)

    def readFromClients(self, clientList):
        for client in clientList:
            err, response = self.receive(client)
            if err:
                continue

            try:
                clientName = client.getpeername()
            except:
                continue

            if clientName not in self.players:
                if response in self.playerNames:
                    print(f'{clientName} tried to join with a non-unique user name')
                    self.send(client, 'Error: User name already taken')
                    # self.removeClient(client)
                    continue

                print(f'{clientName} has joined as {response}')
                self.addPlayer(client, response)
                self.send(client, 'Welcome ' + response)
                continue

            # read states from players

    def writeToClients(self, clientList):
        print(self.getStateMessage())
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
        self.server.bind(('', 0))
        self.server.listen()
        print('Running on port ' + str(self.server.getsockname()[1]))

        while True:
            self.process()

        self.server.close()

if __name__ == '__main__':
    Server().run()