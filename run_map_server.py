#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import random
import json
import uuid
import pickle
from maps_storage import MapsStorage
import icegauntlettool
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
    def __init__(self, maps_storage, dungeon_area):
        self.maps = maps_storage
        self.adapter = self.communicator().createObjectAdapter("DungeonAreaAdapter")
        self.dungeon_area = dungeon_area
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
    
    item_id = 0
    
    def __init__(self, topic, map_data, json_content):
        self.event_channel = topic
        self.map = map_data
        self.json_content = json_content
        self.items = list()
        self.create_items(self.items)
        self.actors = list()    
    
    def getEventChannel(self, current=None):
        return self.event_channel
    
    def getMap(self, current=None):
        return self.actors
    
    def getActors(self, current=None):
        return 'list of actors'
    
    def getItems(self, current=None):
        return self.items
    
    def getNextArea(self, current=None):
        pass
    
    def create_items(self):
        for item in icegauntlettool.get_map_objects(json_content):
            self.items.append(
                IceGauntlet.Item(str(item_id), 
                                 item[0], item[1][0], item[1][1]))
            item_id += 1
    
class DungeonAreaSyncI(IceGauntlet.DungeonAreaSync):
    
    def __init__(self, dungeon_area):
        self.dungeon_area = dungeon_area
    
    def fireEvent(self, event, senderId, current=None):
        try:
            loaded_event = pickle.loads(event)
        except pickle.UnpicklingError as e:
            print('Unexpected error occured')
            
        event_type = loaded_event[0]
        if event_type == 'spawn_actor':
            self.dungeon_area.actors.append(
                IceGauntlet.Actor(loaded_event[1], loaded_event[2]))
        elif event_type == "kill_object":
            self.kill_object(loaded_event[1])
        elif event_type == "open_door":
            door_position = next(filter(lambda item: item.itemId == loaded_event[2], 
                                        self.dungeon_area.getItems()))
            doors = icegauntlettool.search_adjacent_door(
                self.dungeon_area.getItems(), door_position)
        
    def kill_object(self, id):
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
        topic_dungeon_area = str(uuid.uuid1())
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_room_manager_sync)
            topic_areas = topic_mgr.create(topic_dungeon_area)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_mgr.retrieve(topic_room_manager_sync))
        
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

        #Subscription of RoomManagerSync
        topic.subscribeAndGetPublisher(qos, servant_proxy)

        # DungeonArea initialization
        try:
            random_room_name = random.choice(list(maps_storage.get_maps().keys()))
        except IndexError:
            print('No hay ningún mapa actualmente almacenado.')
            return -1
        random_map = maps_storage.get_map(random_room_name)
        random_json_content = maps_storage.read_json(random_room_name)
        servant_dungeon_area = DungeonAreaI(topic_dungeon_area, 
                                            random_map, random_json_content)
        
        #Dungeon initialization
        servant_game = DungeonI(maps_storage, servant_dungeon_area)
        proxy_game = adapter_maps_game.add(
            servant_game, broker.stringToIdentity("Game"))
        
        #DungeonAreaSync initialization
        servant_dungeon_area_sync = DungeonAreaSyncI(servant_dungeon_area)
        adapter_dungeon_area_sync = broker.createObjectAdapter(
            "DungeonAreaSyncAdapter")
        servant_proxy_das = adapter.add(adapter_dungeon_area_sync)
        
        #Subscription of DungeonAreaSync
        topic_areas.subscribeAndGetPublisher(qos, servant_proxy_das)
        
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
