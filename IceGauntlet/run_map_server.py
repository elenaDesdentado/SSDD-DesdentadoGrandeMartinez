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
    def __init__(self, auth_proxy, maps_storage, publisher):

        self.auth_server = IceGauntlet.AuthenticationPrx.checkedCast(auth_proxy)
        self.maps = maps_storage
        self.publisher = publisher

        if not self.auth_server:
            raise RuntimeError('Invalid proxy')

    def publish(self, token, room_data, current=None):
        '''
            Pulish a map file to the server
        '''
        owner = self.auth_server.getOwner(token)
        try:
            new_map = json.loads(room_data)
        #pylint: disable=bare-except
        except:
        #pylint: enable=bare-except
            IceGauntlet.WrongRoomFormat()
        if 'room' not in new_map or 'data' not in new_map:
            raise IceGauntlet.WrongRoomFormat()
        if new_map['room'] in self.maps.get_maps() and self.maps.get_maps()[new_map['room']] != owner:
            raise IceGauntlet.RoomAlreadyExists()

        self.maps.add_map(new_map, owner)

    #pylint: disable=unused-argument
    def remove(self, token, room_name, current=None):
    #pylint: enable=unused-argument
        '''
            Remove a map from the server given its name
        '''
        owner = self.auth_server.getOwner(token)
        # if not self.auth_server.isValid(token):
        #     raise IceGauntlet.Unauthorized()
        # else:
        if room_name not in self.maps.get_maps():
            raise IceGauntlet.RoomNotExists()
        if owner == self.maps.get_maps()[room_name]:
            self.maps.remove_map(room_name)
        else:
            raise IceGauntlet.Unauthorized()

    def availableRooms():
        room_list = list()
        for room, user self.maps.get_maps():
            room_list.append(room + ' ' + user)
        return room_list
    
    def getRoom(self, roomName, current=None):
        json_map = self.maps.get_map(roomName)
        if json_map == None:
            raise IceGauntlet.RoomNotExists();
        else:
            return json_map

class RoomManagerSyncI(IceGauntlet.RoomManagerSync):
    
    def __init__(self, maps_storage, room_manager):
        self.maps = maps_storage
        self.manager_id = ''
        self.room_manager = room_manager

    def hello(self, manager, managerId, current=None):
        if not managerId == self.manager_id:
            self.announce(self.room_manager, self.manager_id)
    
    def announce(self, manager, managerId, current=None):
        announcer_rooms = manager.availableRooms()
        for room_and_user in announcer_rooms:
            room, user = room_and_user.split(' ')
            json_map = manager.getRoom(room)
            self.maps.add_map(json_map, user)
    
    def newRoom(self, roomName,  managerId, current=None):
        pass
    
    def removedRoom(self, roomName, current=None):
        pass

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
    def get_topic_manager(self):
        
        # Podemos pedir una property directamente con propertyToProxy -> el nombre de la property es el asignado a key
        # el TM coge la property y la convierte en proxy -> tenemos la referencia a TM -> Si fuese None, pues la property no esta
        # definida en el archivo
        
        # Le hacemos en el return checkedVCast -> el que tiene que ser one way es el suscriber-publisher, pero con el publisher - topic
        # se le puede hacer
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property '{}' not set".format(key))
            return None

        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, argv):
        '''
            Initialize server written with Ice
        '''
        ## HACERLO EL EQUIVALENTE AL SUSCRIBER, printerserver = equivalente al roommanagersync
        broker = self.communicator()
    
        # Getting topic manager    
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print("Invalid proxy")
            return 2
        
        topic_name = "RoomManagerSyncChannel"
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)
        
        ###### PARTE DEL PUBLISHER #######
        publisher = topic.getPublisher()    # Nos da un proxy sin tipo, que lo que hará será enviar eventos
        room_manager_sync_publisher = IceGauntlet.RoomManagerSyncPrx.uncheckedCast(publisher)   # Para nuestro publisher, el canal implementa la interfaz del printer para poder mandar eventos a los suscribers
        
        # Some calls to methods on room_manager_sync_methods        
        
        maps_storage = MapsStorage()
        servant_maps = RoomManagerI(broker.stringToProxy(argv[1]), maps_storage, room_manager_sync_publisher)
        servant_game = DungeonI()

        servant_roomManagerSync = RoomManagerSyncI(maps_storage, servant_maps)
        adapter = broker.createObjectAdapter("RoomManagerSyncAdapter")
        servant_proxy = adapter.addWithUUID(servant_roomManagerSync)   # proxy del suscriber a registrar al topic
        servant_roomManagerSync.manager_id =  servant_proxy.ice_getIdentity()

        # Suscribe un PROXY al canal de eventos, que es la referencia a un obejto remoto sin tipos
        topic.subscribeAndGetPublisher(qos, servant_proxy)     # Lo que devuelve, mejor no usarlo -> solo lo usamos para suscribir, para obtener un publisher usamos otra
        # servant_maps.publisher.hello(servant_maps, servant_maps.publisher.manager_id)
        room_manager_sync_publisher.hello(servant_maps, servant_roomManagerSync.manager_id)

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
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
        topic.unsubscribe(servant_proxy)   # sacar suscriber del canal al terminar la ejecución -> el topic va a seguir enviandole cosas anque no exista

        return 0

SERVER = Server()
sys.exit(SERVER.main(sys.argv))
