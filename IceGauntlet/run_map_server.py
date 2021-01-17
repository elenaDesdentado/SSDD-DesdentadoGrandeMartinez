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
    def __init__(self, maps_storage, dungeon_area, adapter):
        self.maps = maps_storage
        self.adapter = adapter
        self.dungeon_area = dungeon_area

    #pylint: disable=invalid-name
    #pylint: disable=unused-argument
    def getEntrance(self, current=None):
    #pylint: enable=invalid-name
    #pylint: enable=unused-argument
        '''
            Get a room to be played
        '''
        if len(self.maps.get_maps()) == 0:
            raise IceGauntlet.RoomNotExists()
        else:
            proxy = self.adapter.addWithUUID(self.dungeon_area)
            return IceGauntlet.DungeonAreaPrx.checkedCast(proxy)

class DungeonAreaI(IceGauntlet.DungeonArea):
    
    item_id = 0
    
    def __init__(self, topic_mgr, maps_storage, 
                 adapter_dungeon_area_sync, adapter_dungeon_area):
        self.topic_dungeon_area = str(uuid.uuid1())
        self.topic = topic_mgr
        self.map_storage = maps_storage
        try:
            random_room_name = random.choice(list(maps_storage.get_maps().keys()))
        except IndexError:
            print('No hay ningún mapa actualmente almacenado.')
        self.selected_map = maps_storage.get_map(random_room_name)
        self.json_content = maps_storage.read_json(random_room_name)
        self.adapter_dungeon_area_sync = adapter_dungeon_area_sync
        self.adapter_dungeon_area = adapter_dungeon_area
        self.topic_areas = topic_mgr.create(self.topic_dungeon_area)
        self.items = list()
        self.create_items()
        self.actors = list()
        
        #DungeonAreaSync initialization
        servant_dungeon_area_sync = DungeonAreaSyncI(self)
        self.servant_proxy_das = self.adapter_dungeon_area_sync.addWithUUID(
            servant_dungeon_area_sync)
        self.topic_areas.subscribeAndGetPublisher({}, self.servant_proxy_das)

        #Subscription of DungeonAreaSync
        #self.servant_dungeon_area.topic_areas.subscribeAndGetPublisher({}, servant_proxy_das)

        self.next_area = None
        print(type(self.json_content))
    
    def getEventChannel(self, current=None):
        return self.topic_dungeon_area
    
    def getMap(self, current=None):
        return self.json_content
    
    def getActors(self, current=None):
        return self.actors
    
    def getItems(self, current=None):
        return self.items
    
    def getNextArea(self, current=None):
        if self.next_area is None:
            self.next_area = DungeonAreaI(self.topic, self.map_storage, 
                                          self.adapter_dungeon_area_sync, self.adapter_dungeon_area)
        if len(self.map_storage.get_maps()) == 0:
            raise IceGauntlet.RoomNotExists()
        else:
            proxy = self.adapter_dungeon_area.addWithUUID(self.next_area)
            return IceGauntlet.DungeonAreaPrx.checkedCast(proxy)
    
    def create_items(self):
        for item in icegauntlettool.get_map_objects(self.json_content):
            self.items.append(
                IceGauntlet.Item(str(self.item_id), 
                                 item[0], item[1][0], item[1][1]))
            self.item_id += 1
    
class DungeonAreaSyncI(IceGauntlet.DungeonAreaSync):
    
    def __init__(self, dungeon_area):
        self.dungeon_area = dungeon_area
    
    def fireEvent(self, event, senderId, current=None):
        try:
            loaded_event = pickle.loads(event)
        except pickle.UnpicklingError as e:
            print('Unexpected error occured')
            return
            
        event_type = loaded_event[0]
        if event_type == 'spawn_actor':
            if not loaded_event[1].isnumeric():
                self.dungeon_area.actors.append(
                    IceGauntlet.Actor(loaded_event[1], loaded_event[2]))
        elif event_type == "kill_object":
            self.kill_object(loaded_event[1])
        elif event_type == "open_door":
            door_position = next(filter(lambda item: item.itemId == loaded_event[2], 
                                        self.dungeon_area.getItems()))
            items_dict = dict()
            for item in self.dungeon_area.items:
                items_dict[item.itemId] = (item.itemType, (item.positionX, item.positionY))
            doors = icegauntlettool.search_adjacent_door(items_dict, door_position)
            for door in doors:
                self.kill_object(door)

    def kill_object(self, id):
        index = -1
        if id.isnumeric():
            object_list = self.dungeon_area.items
            for i, item in enumerate(object_list):
                if item.itemId == id:
                    index = i
                    break
        else:
            object_list = self.dungeon_area.actors
            for i, actor in enumerate(object_list):
                if actor.actorId == id:
                    index = i
                    break
        if index > -1:
            del object_list[index]

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
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_room_manager_sync)
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

        # Subscription of RoomManagerSync
        topic.subscribeAndGetPublisher(qos, servant_proxy)

        # DungeonArea initialization
        adapter_dungeon_area_sync = broker.createObjectAdapter(
            "DungeonAreaSyncAdapter")
        dungeon_area_adapter = broker.createObjectAdapter(
            "DungeonAreaAdapter")
        servant_dungeon_area = DungeonAreaI(topic_mgr, maps_storage, 
                                            adapter_dungeon_area_sync, dungeon_area_adapter)
        
        #Dungeon initialization
        servant_game = DungeonI(maps_storage, 
                                servant_dungeon_area, dungeon_area_adapter)
        proxy_game = adapter_maps_game.add(
            servant_game, broker.stringToIdentity("Game"))
        
        room_manager_sync_publisher.hello(casted_proxy_maps, servant_roomManagerSync.manager_id)

        with open(PROXY_GAME_FILE, 'w', encoding='UTF-8') as file_handler:
            file_handler.write('"' + str(proxy_game) + '"\n')
        
        adapter_maps_game.activate()
        adapter.activate()
        adapter_dungeon_area_sync.activate()
        dungeon_area_adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        
        topic.unsubscribe(servant_proxy)

        return 0

SERVER = Server()
sys.exit(SERVER.main(sys.argv))
