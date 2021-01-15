import json
import os

MAPS_DB = "./maps.json"
MAPS_FOLDER = "./maps/"
MAPS_REMOVED_FOLDER = "./removed_maps/"

class MapsStorage():
    
    def __init__(self):
        self.maps = dict()
        with open(MAPS_DB, 'r', encoding='UTF-8') as maps_file_handler:
            self.maps = json.load(maps_file_handler)
    
    def add_map(self, new_map, owner):
        with open('{0}{1}.{2}'.format(MAPS_FOLDER, new_map['room'], 'json'), 'w', encoding='UTF-8') as new_map_file:
            json.dump(new_map, new_map_file)
        self.maps[new_map['room']] = owner 
        with open(MAPS_DB, 'w', encoding='UTF-8') as maps_file_handler:
            json.dump(self.maps, maps_file_handler, indent=2)
            
    def get_maps(self):
        return self.maps
    
    def get_map(self, room_name):
        if room_name in self.maps:
            with open('{0}{1}.{2}'.format(MAPS_FOLDER, room_name, 'json'), 'r', encoding='UTF-8') as map_file:
                return json.load(map_file)
        else:
            return None
        
    def remove_map(self, room_name):
        del self.maps[room_name]
        os.replace('{0}{1}.{2}'.format(MAPS_FOLDER, room_name, 'json'),
                    '{0}{1}.{2}'.format(MAPS_REMOVED_FOLDER, room_name, 'json'))
        with open(MAPS_DB, 'w', encoding='UTF-8') as maps_file_handler:
            json.dump(self.maps, maps_file_handler, indent=2)
            
    def read_json(self, room_name):
        if room_name in self.maps:
            with open('{0}{1}.{2}'.format(MAPS_FOLDER, room_name, 'json'), 'r', encoding='UTF-8') as map_file:
                return json.dumps(json.load(map_file))
        else:
            return None
        