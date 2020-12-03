#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import os
import random
import Ice
import json
Ice.loadSlice('IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413

MAPS_DB = "./maps.json"
MAPS_FOLDER = "./maps/"
MAPS_REMOVED_FOLDER = "./removed_maps/"
PROXY_GAME_FILE = "proxy_game"

if len(sys.argv) != 3:
    for arg in sys.argv:
        print(arg)
    print('Usage: ./run_map_server.py <auth_server_proxy> --Ice.Config=run_map_server.conf')
    sys.exit(-1)

class RoomManagerI(IceGauntlet.RoomManager):
    
    def __init__(self, authProxy):
        
        self.auth_server = IceGauntlet.AuthenticationPrx.checkedCast(authProxy)
        self.maps = dict()
        
        if not self.auth_server:
            raise RuntimeError('Invalid proxy')
        with open(MAPS_DB, 'r', encoding='UTF-8') as mapsFileHandler:
            self.maps = json.load(mapsFileHandler)
    
    def publish(self, token, roomData, current=None):
        if not(self.auth_server.isValid(token)):
            raise IceGauntlet.Unauthorized()
        else:
            try:
                new_map = json.loads(roomData)
            except: 
                IceGauntlet.WrongRoomFormat()
            if 'room' not in new_map or 'data' not in new_map:
                raise IceGauntlet.WrongRoomFormat()   
            if new_map['room'] in self.maps and self.maps[new_map['room']] != token:
                raise IceGauntlet.RoomAlreadyExists()
            with open('{0}{1}.{2}'.format(MAPS_FOLDER, new_map['room'], 'json'), 'w', encoding='UTF-8') as newMapFile:
                json.dump(new_map, newMapFile)
            self.maps[new_map['room']] = token
            with open(MAPS_DB, 'w', encoding='UTF-8') as mapsFileHandler:
                json.dump(self.maps, mapsFileHandler, indent=2)
             
        
    def remove(self, token, roomName, current=None):
        if not(self.auth_server.isValid(token)):
            raise IceGauntlet.Unauthorized()
        else:
            # Comprobar si el roomName es una de las llaves de maps
            if roomName not in self.maps:
                raise IceGauntlet.RoomNotExists()
            if token == self.maps[roomName]:
                del self.maps[roomName]
                os.replace('{0}{1}.{2}'.format(MAPS_FOLDER, roomName, 'json'), '{0}{1}.{2}'.format(MAPS_REMOVED_FOLDER, roomName, 'json'))
                with open(MAPS_DB, 'w', encoding='UTF-8') as mapsFileHandler:
                    json.dump(self.maps, mapsFileHandler, indent=2)
            else:
                raise IceGauntlet.Unauthorized()
            

class DungeonI(IceGauntlet.Dungeon):

    def getRoom(self, current=None):
        selected_room = None
        with open(MAPS_DB, 'r', encoding='UTF-8') as mapsFileHandler:
            maps = json.load(mapsFileHandler)
            if len(maps.keys()) <= 0:
                raise IceGauntlet.RoomNotExists()
            
            selected_room = random.choice(list(maps.keys()))
                
        with open('{0}{1}.{2}'.format(MAPS_FOLDER, selected_room, 'json'), 'r', encoding='UTF-8') as mapFileHandler:
            roomData = mapFileHandler.read()
            
        return roomData
        

class Server(Ice.Application):
    
    def run(self, argv):
        broker = self.communicator()
        servant_maps = RoomManagerI(broker.stringToProxy(argv[1]))
        servant_game = DungeonI()

        adapter_maps_game = broker.createObjectAdapter("MapsGameAdapter")
        proxy_maps = adapter_maps_game.add(servant_maps, broker.stringToIdentity("Maps"))
        proxy_game = adapter_maps_game.add(servant_game, broker.stringToIdentity("Game"))

        print('"' + str(proxy_maps) + '"' , flush=True) 
        
        with open(PROXY_GAME_FILE, 'w', encoding='UTF-8') as fileHandler:
            fileHandler.write('"' + str(proxy_game) + '"\n') 
            
        adapter_maps_game.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

server = Server()
sys.exit(server.main(sys.argv))
