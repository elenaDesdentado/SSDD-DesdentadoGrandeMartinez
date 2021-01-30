
'''
    Storage of maps for room managers
'''

import json
import os

MAPS_DB = "/maps.json"
MAPS_FOLDER = "/maps/"
MAPS_REMOVED_FOLDER = "/removed_maps/"

class MapsStorage():
    '''
        Class holding functions over the maps storage
    '''
    def __init__(self, base_dir):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir + MAPS_FOLDER) or not os.path.isdir(self.base_dir + MAPS_FOLDER):
            os.mkdir(self.base_dir + MAPS_FOLDER)
        if not os.path.exists(self.base_dir + MAPS_REMOVED_FOLDER) or not os.path.isdir(self.base_dir + MAPS_REMOVED_FOLDER):
            os.mkdir(self.base_dir + MAPS_REMOVED_FOLDER)
        if not os.path.exists(self.base_dir + MAPS_DB) or not os.path.isfile(self.base_dir + MAPS_DB):
            with open(self.base_dir + MAPS_DB, 'w', encoding='UTF-8') as maps_file_handler:
                json.dump({}, maps_file_handler, indent=2)
        self.maps = dict()
        with open(self.base_dir + MAPS_DB, 'r', encoding='UTF-8') as maps_file_handler:
            self.maps = json.load(maps_file_handler)

    def add_map(self, new_map, owner):
        '''
        Add a new map to the storage
        '''
        print(os.getcwd())
        print('{0}{1}.{2}'.format(self.base_dir + MAPS_FOLDER, new_map['room'], 'json'))
        with open('{0}{1}.{2}'.format(self.base_dir + MAPS_FOLDER, new_map['room'], 'json'),
        'w', encoding='UTF-8') as new_map_file:
            json.dump(new_map, new_map_file)
        self.maps[new_map['room']] = owner
        with open(self.base_dir + MAPS_DB, 'w', encoding='UTF-8') as maps_file_handler:
            json.dump(self.maps, maps_file_handler, indent=2)

    def get_maps(self):
        '''
        Get all the maps stored
        '''
        return self.maps

    def get_map(self, room_name):
        '''
        Get a stored mapped given its name
        '''
        print('Mapas acltualmente almacenados en ', os.getcwd(), ': ', self.maps)
        if room_name in self.maps:
            with open('{0}{1}.{2}'.format(self.base_dir + MAPS_FOLDER, room_name, 'json'),
            'r', encoding='UTF-8') as map_file:
                try:
                    return json.load(map_file)
                except Exception as e:
                    print('exception at loading in get_map')
                    print("get_map " + room_name)
                    print(e)
                    print('exception at loading in get_map')
                    raise Exception('exception at loading in get_map')
        else:
            return None

    def remove_map(self, room_name):
        '''
        Delete a map from the storage given its name
        '''
        del self.maps[room_name]
        os.replace('{0}{1}.{2}'.format(self.base_dir + MAPS_FOLDER, room_name, 'json'),
        '{0}{1}.{2}'.format(self.base_dir + MAPS_REMOVED_FOLDER, room_name, 'json'))
        with open(MAPS_DB, 'w', encoding='UTF-8') as maps_file_handler:
            json.dump(self.maps, maps_file_handler, indent=2)

    def read_json(self, room_name):
        '''
        Gives the json file data where maps are stored
        '''
        if room_name in self.maps:
            with open('{0}{1}.{2}'.format(self.base_dir + MAPS_FOLDER, room_name, 'json'),
            'r', encoding='UTF-8') as map_file:
                return json.dumps(json.load(map_file))
        else:
            return None
