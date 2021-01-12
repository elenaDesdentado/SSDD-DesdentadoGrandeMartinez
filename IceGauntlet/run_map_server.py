#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import random
import json
from maps_storage import MapsStorage
# pylint: disable=import-error
import Ice
import IceStorm
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
        self.manager_id = ''

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
        self.publisher.newRoom(new_map['room'], self.manager_id)

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
            self.publisher.removedRoom(room_name)
        else:
            raise IceGauntlet.Unauthorized()

    def availableRooms(self, current=None):
        room_list = list()
        for room in self.maps.get_maps():
            room_list.append(room + ' ' + self.maps.get_maps()[room])
        
        return room_list
    
    def getRoom(self, roomName, current=None):
        json_map = self.maps.get_map(roomName)
        if json_map == None:
            raise IceGauntlet.RoomNotExists()
        else:
            user = self.maps.get_maps()[roomName]
            return json.dumps(json_map) + '_' + user    #Puede fallar

class RoomManagerSyncI(IceGauntlet.RoomManagerSync):
    
    def __init__(self, maps_storage, room_manager, casted_proxy_maps):
        self.maps = maps_storage
        self.manager_id = ''
        self.room_manager = room_manager
        self.managers = dict()
        self.casted_proxy_maps = casted_proxy_maps

    def hello(self, manager, managerId, current=None):
        if not managerId == self.manager_id:
            self.managers[managerId] = manager
            self.room_manager.publisher.announce(self.casted_proxy_maps, self.manager_id)
    
    def announce(self, manager, managerId, current=None):
        announcer_rooms = manager.availableRooms()
        self.managers[managerId] = manager
        if not managerId == self.manager_id:
            for room_and_user in announcer_rooms:
                room, user = room_and_user.split(' ')
                json_map_and_user = manager.getRoom(room)
                json_map, user = json_map_and_user.split('_')
                new_map = json.loads(json_map)
                self.maps.add_map(new_map, user)
    
    def newRoom(self, roomName,  managerId, current=None):
        manager_new_map = self.managers[managerId]
        json_map_and_user = manager_new_map.getRoom(roomName)
        json_map, user = json_map_and_user.split('_')
        new_map = json.loads(json_map)
        self.maps.add_map(new_map, user)
    
    def removedRoom(self, roomName, current=None):
        self.maps.remove_map(roomName)
    
class DungeonI(IceGauntlet.Dungeon):
    '''
        Implements Dungeon interface
    '''
    def __init__(self, maps_storage):
        self.maps = maps_storage
        self.adapter = self.communicator().createObjectAdapter("DungeonAreaAdapter")
        self.dungeon_area = DungeonAreaI("DungeonAreaSyncChannel")
    #pylint: disable=invalid-name
    #pylint: disable=unused-argument
    def getEntrance(self, current=None):
    #pylint: enable=invalid-name
    #pylint: enable=unused-argument
        '''
            Get a room to be played
        '''
        selected_room = None
        if len(self.maps.get_maps()) == 0:
            raise IceGauntlet.RoomNotExists()
        else:
            proxy = adapter.add(self.gungeon_area)
            return IceGauntlet.DungeonAreaPrx.checkedCast(proxy)

class DungeonAreaI(IceGauntlet.DungeonArea):
    
    def __init__(self, topic):
        self.event_channel = topic
    
    def getEventChannel(self, current=None):
        return self.event_channel
    
    def getMap(self, current=None):
        return ''
    
    def getActor(self, current=None):
        return 'list of actors'
    
    def getItems(self, current=None):
        return 'list of objects'
    
    def getNextArea(self, current=None):
        pass
    
class DungeonAreaSyncI(IceGauntlet.DungeonAreaSync):
    def fireEvent(self, event, senderId, current=None):
        pass

class Server(Ice.Application):
    '''
        Server that hosts Dungeon and RoomManager services
    '''
    def get_topic_manager(self):
    
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property '{}' not set".format(key))
            return None
        
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, argv):
        '''
            Initialize server written with Ice
        '''
        broker = self.communicator()
    
        # Getting topic manager    
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print("Invalid proxy")
            return 2
        
        topic_room_manager_sync = "RoomManagerSyncChannel"
        topic_dungeon_area = "DungeonAreaSyncChannel"
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_room_manager_sync)
            topic_areas = topic_mgr.retrieve(topic_dungeon_area)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_mgr.retrieve(topic_room_manager_sync))
            topic_areas = topic_mgr.retrieve(topic_dungeon_area)
        
        ###### PARTE DEL PUBLISHER #######
        publisher = topic.getPublisher()
        room_manager_sync_publisher = IceGauntlet.RoomManagerSyncPrx.uncheckedCast(publisher)

        # RoomManager initialization
        maps_storage = MapsStorage()
        servant_maps = RoomManagerI(broker.stringToProxy(argv[1]), maps_storage, room_manager_sync_publisher)
        adapter_maps_game = broker.createObjectAdapter("MapsGameAdapter")
        proxy_maps = adapter_maps_game.add(
            servant_maps, broker.stringToIdentity("Maps"))
        casted_proxy_maps = IceGauntlet.RoomManagerPrx.uncheckedCast(proxy_maps)
        
        print('\"' + str(proxy_maps) + '\"')
        
        # RoomManagerSync
        servant_roomManagerSync = RoomManagerSyncI(maps_storage, servant_maps, casted_proxy_maps)
        adapter = broker.createObjectAdapter("RoomManagerSyncAdapter")
        servant_proxy = adapter.addWithUUID(servant_roomManagerSync)
        identity =  servant_proxy.ice_getIdentity()
        servant_roomManagerSync.manager_id = broker.identityToString(identity)
        servant_maps.manager_id = broker.identityToString(identity)

        topic.subscribeAndGetPublisher(qos, servant_proxy)

        #Dungeon initialization
        servant_game = DungeonI(maps_storage)
        proxy_game = adapter_maps_game.add(
            servant_game, broker.stringToIdentity("Game"))
        
        #DungeonAreaSync initialization
        servant_dungeon_area_sync = DungeonAreaSyncI()
        adapter_dungeon_area_sync = broker.createObjectAdapter(
            "DungeonAreaSyncAdapter")
        servant_proxy_das = adapter.add(adapter_dungeon_area_sync)
        
        room_manager_sync_publisher.hello(casted_proxy_maps, servant_roomManagerSync.manager_id)

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