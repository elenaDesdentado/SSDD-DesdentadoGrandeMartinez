#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import random
import json
# pylint: disable=import-error
import Ice
Ice.loadSlice('IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
# pylint: disable=too-few-public-methods
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413

MAPS_DB = "./maps.json"
MAPS_FOLDER = "./maps/"
MAPS_REMOVED_FOLDER = "./removed_maps/"
PROXY_GAME_FILE = "proxy_game"

'''
    Run map server for IceGauntlet
'''

if len(sys.argv) != 3:
    for arg in sys.argv:
        print(arg)
    print('Usage: ./run_map_server.py <auth_server_proxy> --Ice.Config=run_map_server.conf')
    sys.exit(-1)

class RoomManagerI(IceGauntlet.RoomManager):
    '''
        Implements RoomManager interface
    '''
    def __init__(self, auth_proxy):

        self.auth_server = IceGauntlet.AuthenticationPrx.checkedCast(auth_proxy)
        self.maps = dict()

        if not self.auth_server:
            raise RuntimeError('Invalid proxy')
        with open(MAPS_DB, 'r', encoding='UTF-8') as maps_file_handler:
            self.maps = json.load(maps_file_handler)

    def publish(self, token, room_data, current=None):
        '''
            Pulish a map file to the server
        '''
        if not self.auth_server.isValid(token):
            raise IceGauntlet.Unauthorized()
        else:
            try:
                new_map = json.loads(room_data)
            #pylint: disable=bare-except
            except:
            #pylint: enable=bare-except
                IceGauntlet.WrongRoomFormat()
            if 'room' not in new_map or 'data' not in new_map:
                raise IceGauntlet.WrongRoomFormat()
            if new_map['room'] in self.maps and self.maps[new_map['room']] != token:
                raise IceGauntlet.RoomAlreadyExists()
            with open('{0}{1}.{2}'.format(MAPS_FOLDER, new_map['room'], 'json'), 'w', encoding='UTF-8') as new_map_file:
                json.dump(new_map, new_map_file)
            self.maps[new_map['room']] = token
            with open(MAPS_DB, 'w', encoding='UTF-8') as maps_file_handler:
                json.dump(self.maps, maps_file_handler, indent=2)

    #pylint: disable=unused-argument
    def remove(self, token, room_name, current=None):
    #pylint: enable=unused-argument
        '''
            Remove a map from the server given its name
        '''
        if not self.auth_server.isValid(token):
            raise IceGauntlet.Unauthorized()
        else:
            if room_name not in self.maps:
                raise IceGauntlet.RoomNotExists()
            if token == self.maps[room_name]:
                del self.maps[room_name]
                #pylint: disable=no-member
                os.replace('{0}{1}.{2}'.format(MAPS_FOLDER, room_name, 'json'),
                           '{0}{1}.{2}'.format(MAPS_REMOVED_FOLDER, room_name, 'json'))
                with open(MAPS_DB, 'w', encoding='UTF-8') as maps_file_handler:
                    json.dump(self.maps, maps_file_handler, indent=2)
            else:
                raise IceGauntlet.Unauthorized()


class DungeonI(IceGauntlet.Dungeon):
    '''
        Implements Dungeon interface
    '''
    #pylint: disable=invalid-name
    #pylint: disable=unused-argument
    def getRoom(self, current=None):
    #pylint: enable=invalid-name
    #pylint: enable=unused-argument
        '''
            Get a room to be played
        '''
        selected_room = None
        with open(MAPS_DB, 'r', encoding='UTF-8') as maps_file_handler:
            maps = json.load(maps_file_handler)
            if len(maps.keys()) <= 0:
                raise IceGauntlet.RoomNotExists()

            selected_room = random.choice(list(maps.keys()))

        with open('{0}{1}.{2}'.format(MAPS_FOLDER, selected_room, 'json'), 'r', encoding='UTF-8') as map_file_handler:
            room_data = map_file_handler.read()

        return room_data


class Server(Ice.Application):
    '''
        Server that hosts Dungeon and RoomManager services
    '''
    def run(self, argv):
        '''
            Initialize server written with Ice
        '''
        broker = self.communicator()
        servant_maps = RoomManagerI(broker.stringToProxy(argv[1]))
        servant_game = DungeonI()

        adapter_maps_game = broker.createObjectAdapter("MapsGameAdapter")
        proxy_maps = adapter_maps_game.add(
            servant_maps, broker.stringToIdentity("Maps"))
        proxy_game = adapter_maps_game.add(
            servant_game, broker.stringToIdentity("Game"))

        print('"{0}"'.format(str(proxy_maps)))
        #print('"' + str(proxy_maps) + '"', flush=True)

        with open(PROXY_GAME_FILE, 'w', encoding='UTF-8') as file_handler:
            file_handler.write('"' + str(proxy_game) + '"\n')

        adapter_maps_game.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


SERVER = Server()
sys.exit(SERVER.main(sys.argv))
