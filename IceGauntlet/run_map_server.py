#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

'''
    Server holding maps and game management for IceGauntlet
'''

# pylint: disable=W0410
from __future__ import print_function
# pylint: enable=W0410
import sys
import random
import json
import uuid
import pickle
# pylint: disable=import-error
import Ice
import icegauntlettool
from maps_storage import MapsStorage
import IceStorm
Ice.loadSlice('IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
# pylint: disable=too-few-public-methods
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413

PROXY_GAME_FILE = "proxy_game"


# if len(sys.argv) != 3:
#     for arg in sys.argv:
#         print(arg)
#     print('Usage: ./run_map_server.py <auth_server_proxy> --Ice.Config=run_map_server.conf')
#     sys.exit(-1)

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
        #pylint: disable=W0613
        #pylint: enable=W0613
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
        if (new_map['room'] in self.maps.get_maps() and
            self.maps.get_maps()[new_map['room']] != owner):
            raise IceGauntlet.RoomAlreadyExists()

        self.maps.add_map(new_map, owner)
        self.publisher.newRoom(new_map['room'], self.manager_id)

    def remove(self, token, room_name, current=None):
        #pylint: disable=W0613
        #pylint: enable=W0613
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
        #pylint: disable=C0103, W0613
        #pylint: enable=C0103, W0613
        '''
            Returns a list of available rooms names
        '''
        print('available rooms before the loop')
        room_list = list()
        for room in self.maps.get_maps():
            room_list.append(room + ' ' + self.maps.get_maps()[room])
        print('Available rooms in ', self.manager_id, ': ', room_list)
        return room_list

    def getRoom(self, roomName, current=None):
        #pylint: disable=C0103, W0613
        #pylint: enable=C0103, W0613
        '''
            Gets the content of the json file holding the map given
        '''
        json_map = self.maps.get_map(roomName)
        if json_map is None:
            raise IceGauntlet.RoomNotExists()

        user = self.maps.get_maps()[roomName]
        print(roomName + '_' + user)
        return json.dumps(json_map) + '_' + user

class RoomManagerSyncI(IceGauntlet.RoomManagerSync):
    '''
        Event channel for the several RoomManagers
    '''
    def __init__(self, maps_storage, room_manager, casted_proxy_maps):
        self.maps = maps_storage
        self.manager_id = ''
        self.room_manager = room_manager
        self.managers = dict()
        self.casted_proxy_maps = casted_proxy_maps

    def hello(self, manager, managerId, current=None):
        #pylint: disable=W0613, C0103
        #pylint: enable=W0613, C0103
        '''
            Handler for the hello event
        '''
        if not managerId == self.manager_id:
            print('hello recibido')
            self.managers[managerId] = manager
            self.room_manager.publisher.announce(self.casted_proxy_maps, self.manager_id)

    def announce(self, manager, managerId, current=None):
        #pylint: disable= unused-argument, C0103
        #pylint: enable= unused-argument, C0103
        '''
            Handler for the announce event
        '''
        if not managerId == self.manager_id:
            print('announce recibido')
            print('manager:', manager, ' id: ', managerId)
            announcer_rooms = manager.availableRooms()
            print(managerId, 'mis rooms:', announcer_rooms)
            self.managers[managerId] = manager
            print('Managers registrados: ', self.managers)
            for room_and_user in announcer_rooms:
                room, user = room_and_user.split(' ')
                json_map_and_user = manager.getRoom(room)
                json_map, user = json_map_and_user.split('_')
                new_map = json.loads(json_map)
                self.maps.add_map(new_map, user)

    def newRoom(self, roomName,  managerId, current=None):
        #pylint: disable=W0613, C0103
        #pylint: enable=W0613, C0103
        '''
            Handler for the newRoom event
        '''
        if managerId != self.manager_id:
            print('newRoom recibido de: ', managerId, ' ', roomName)
            manager_new_map = self.managers[managerId]
            print('Managers actuales: ', self.managers)
            print('Antes de getRoom, ejecuta ', manager_new_map, ' del tipo ', type(manager_new_map))
            # Por alguna razon, esta llamada es como es como si la ejecutase el 
            # roomManager asociado al servicio que la recibe: si el nuevo room se lo suben a
            # roomManager2, su proxy asociado deberia ser el que ejecutase el getRoom(), 
            # pero parece que lo ejecuta el que lo recibe (en este caso roomManager1):
            # newRoom recibido
            # before manager_new_map.getRoom  58F0F938-68EF-41FC-B32B-CDAEE22A16DA   level2
            # Mapas acltualmente almacenados en  /tmp/db/node1/distrib/IceGauntlet :  {'level1': 'elena-desdentado'}
            # newRoom recibido de:  30C04811-A0B5-4D87-B5F6-7F0050DA9A6F   level2
            # Managers actuales:  {'30C04811-A0B5-4D87-B5F6-7F0050DA9A6F': room_manager -t -e 1.1 @ ReplicatedRoomManager, 'FDA32ADF-8B64-44FD-A59F-A4EC49A19A8A': room_manager -t -e 1.1 @ ReplicatedRoomManager}
            # Antes de getRoom, ejecuta  room_manager -t -e 1.1 @ ReplicatedRoomManager  del tipo  <class 'IceGauntlet.RoomManagerPrx'>
            # Mapas acltualmente almacenados en  /tmp/db/node2/distrib/IceGauntlet :  {'level1': 'elena-desdentado'}
            # En este ultimo caso el evento fue en esta direccion: roomManager1 ----> roommanager3
            # Resultado: maps.json de roomManager1 actualizado, el de roomManager3
            json_map_and_user = manager_new_map.getRoom(roomName) 
            print('after manager_new_map.getRoom')
            json_map, user = json_map_and_user.split('_')
            print('_'+json_map[:50])
            print('_'+user)
            new_map = json.loads(json_map)
            self.maps.add_map(new_map, user)

    def removedRoom(self, roomName, current=None):
        #pylint: disable=W0613
        #pylint: disable=C0103
        #pylint: enable=W0613
        #pylint: enable=C0103
        '''
            Handler for the removedRoom event
        '''
        print('removedRoom recibido')
        if roomName in self.maps.get_maps():
            self.maps.remove_map(roomName)

class DungeonI(IceGauntlet.Dungeon):
    '''
        Implements Dungeon interface
    '''
    def __init__(self, maps_storage, dungeon_area, adapter):
        self.maps = maps_storage
        self.adapter = adapter
        self.dungeon_area = dungeon_area

    def getEntrance(self, current=None):
    #pylint: disable=C0103
    #pylint: disable=W0613
    #pylint: enable=C0103
    #pylint: enable=W0613
        '''
            Get a room to be played
        '''
        if len(self.maps.get_maps()) == 0:
            raise IceGauntlet.RoomNotExists()
        proxy = self.adapter.addWithUUID(self.dungeon_area)
        return IceGauntlet.DungeonAreaPrx.checkedCast(proxy)

class DungeonAreaI(IceGauntlet.DungeonArea):
    #pylint: disable=R0902
    #pylint: enable=R0902
    '''
        Dungeon maps representation on the multiplayer game
    '''
    item_id = 0

    def __init__(self, topic_mgr, maps_storage,
                 adapter_dungeon_area_sync, adapter_dungeon_area):
        self.topic_dungeon_area = str(uuid.uuid1())
        self.topic = topic_mgr
        self.map_storage = maps_storage
        self.json_content = None 
        self.adapter_dungeon_area_sync = adapter_dungeon_area_sync
        self.adapter_dungeon_area = adapter_dungeon_area
        self.topic_areas = topic_mgr.create(self.topic_dungeon_area)
        self.items = list()
        self.actors = list()

        #DungeonAreaSync initialization
        servant_dungeon_area_sync = DungeonAreaSyncI(self)
        self.servant_proxy_das = self.adapter_dungeon_area_sync.addWithUUID(
            servant_dungeon_area_sync)
        self.topic_areas.subscribeAndGetPublisher({}, self.servant_proxy_das)

        self.next_area = None

    def getEventChannel(self, current=None):
        #pylint: disable=C0103, W0613
        #pylint: enable=C0103, W0613
        '''
            Get event channel associated to current  DungeonArea
        '''
        return self.topic_dungeon_area

    def getMap(self, current=None):
        #pylint: disable=C0103, W0613
        #pylint: enable=C0103, W0613
        '''
            Get current map data of the DungeonArea
        '''
        if self.json_content is None:
            try:
                random_room_name = random.choice(list(self.map_storage.get_maps().keys()))
            except IndexError:
                raise IceGauntlet.RoomNotExists()
            self.json_content = self.map_storage.read_json(random_room_name)
            self.create_items()
        return self.json_content

    def getActors(self, current=None):
        #pylint: disable=W0613, C0103
        '''
            Get current list of actors of the DungeonArea
        '''
        #pylint: enable=W0613, C0103
        return self.actors

    def getItems(self, current=None):
        #pylint: disable=W0613, C0103
        '''
            Get current list of items of the DungeonArea
        '''
        #pylint: enable=W0613, C0103
        return self.items

    def getNextArea(self, current=None):
        #pylint: disable=W0613, C0103
        '''
            Gives the next DungeonArea to player that has completed current one
        '''
        #pylint: enable=W0613, C0103
        if self.next_area is None:
            self.next_area = DungeonAreaI(self.topic, self.map_storage,
            self.adapter_dungeon_area_sync, self.adapter_dungeon_area)
        if len(self.map_storage.get_maps()) == 0:
            raise IceGauntlet.RoomNotExists()
        proxy = self.adapter_dungeon_area.addWithUUID(self.next_area)
        return IceGauntlet.DungeonAreaPrx.checkedCast(proxy)

    def create_items(self):
        '''
            Creates the list of items of the current DungeonArea
        '''
        for item in icegauntlettool.get_map_objects(self.json_content):
            self.items.append(
            IceGauntlet.Item(str(self.item_id),
            item[0], item[1][0], item[1][1]))
            self.item_id += 1

class DungeonAreaSyncI(IceGauntlet.DungeonAreaSync):
    '''
        Event channel for a single DungeonArea
    '''
    def __init__(self, dungeon_area):
        self.dungeon_area = dungeon_area

    def fireEvent(self, event, senderId, current=None):
        #pylint: disable=C0103, W0613
        #pylint: enable=C0103, W0613
        '''
            Reception of an event sent by a client playing IceGauntlet
        '''
        try:
            loaded_event = pickle.loads(event)
        except pickle.UnpicklingError:
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

    def kill_object(self, _id):
        #pylint: disable= invalid-name
        #pylint: enable= invalid-name
        '''
            Deletes an object from the Items list of a DungeonArea
        '''
        index = -1
        if _id.isnumeric():
            object_list = self.dungeon_area.items
            for i, item in enumerate(object_list):
                if item.itemId == _id:
                    index = i
                    break
        else:
            object_list = self.dungeon_area.actors
            for i, actor in enumerate(object_list):
                if actor.actorId == _id:
                    index = i
                    break
        if index > -1:
            del object_list[index]

class Server(Ice.Application):
    '''
        Server that hosts Dungeon and RoomManager services
    '''
    def get_topic_manager(self):
        '''
            Gets the topic manager from IceStorm service
        '''
        #key = 'IceGauntlet.IceStorm.TopicManager'
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        #proxy = self.communicator().stringToProxy('IceGauntlet.IceStorm/TopicManager')
        if proxy is None:
            print("property '{}' not set".format(key))
            return None

        #pylint: disable=no-member
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
        #pylint: enable=no-member

    def run(self, args):
        #pylint: disable=W0613, too-many-locals
        #pylint: enable=W0613, too-many-locals
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
        #pylint: disable=no-member
        except IceStorm.NoSuchTopic:
        #pylint: enable=no-member
            topic = topic_mgr.create(topic_room_manager_sync)

        ###### PARTE DEL PUBLISHER #######
        publisher = topic.getPublisher()
        room_manager_sync_publisher = IceGauntlet.RoomManagerSyncPrx.uncheckedCast(publisher)

        # RoomManager initialization
        maps_storage = MapsStorage()
        auth_server = broker.getProperties().getProperty('AuthServer')
        auth_server_split = auth_server.split('\"')
        servant_maps = RoomManagerI(broker.stringToProxy(auth_server_split[0]),
                                    maps_storage, room_manager_sync_publisher)
        adapter_maps_game = broker.createObjectAdapter("MapsGameAdapter")
        _id_room_manager = broker.getProperties().getProperty('Identity') ######
        proxy_maps = adapter_maps_game.add(
            servant_maps, broker.stringToIdentity(_id_room_manager)) ######
        proxy_maps_direct = adapter_maps_game.add(
            servant_maps, broker.stringToIdentity(broker.getProperties().getProperty('Ice.ProgramName')))
        casted_proxy_maps = IceGauntlet.RoomManagerPrx.uncheckedCast(proxy_maps_direct)

        print('Proxy individual : ', proxy_maps_direct) ######
        print('\"' + str(proxy_maps) + '\"')

        # RoomManagerSync
        servant_room_manager_sync = RoomManagerSyncI(maps_storage, servant_maps, casted_proxy_maps)
        adapter = broker.createObjectAdapter("RoomManagerSyncAdapter")
        servant_proxy = adapter.addWithUUID(servant_room_manager_sync)
        identity =  servant_proxy.ice_getIdentity()
        servant_room_manager_sync.manager_id = broker.identityToString(identity)
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

        adapter_maps_game.activate()
        adapter.activate()
        adapter_dungeon_area_sync.activate()
        dungeon_area_adapter.activate()
        
        room_manager_sync_publisher.hello(casted_proxy_maps, servant_room_manager_sync.manager_id)
        print('ejecutado hello desde run')

        with open(PROXY_GAME_FILE, 'w', encoding='UTF-8') as file_handler:
            file_handler.write('"' + str(proxy_game) + '"\n')

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        topic.unsubscribe(servant_proxy)

        return 0

SERVER = Server()
sys.exit(SERVER.main(sys.argv))
