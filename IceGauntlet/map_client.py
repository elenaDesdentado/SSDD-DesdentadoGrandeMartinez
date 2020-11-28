#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import Ice
Ice.loadSlice('IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413

OPTION_PUBLISH_MAP = 'publishmap'
OPTION_DELETE_MAP = 'deletemap'

# ¿Queda aqui bien la comprobacion de los argumentos?   
if len(sys.argv) != 4:
    print('Usage: ./map_client.py <map_server_proxy> <token> <JSON_map_file> <option>>, <option> can be {0} or {1}'.format(OPTION_PUBLISH_MAP, OPTION_DELETE_MAP))
    sys.exit(-1)
    
class MapClient(Ice.Application):
    def run(self, argv):
        proxy = self.communicator().stringToProxy(argv[1])  # map_server proxy
        token = argv[2]
        map_file = argv[3]
        option = argv[4].lower()
        
        map_server = IceGauntlet.AuthenticationPrx.checkedCast(proxy)

        if not map_server:
            raise RuntimeError('Invalid proxy')
        
        if option == OPTION_PUBLISH_MAP:
            #roomData = "./nivel01.json"
            with open(map_file, 'r', encoding='UTF-8') as mapFileHandler:
                # mapDictionary = json.load(mapFileHandler)
                roomData = mapFileHandler.read() # mapDictionary['data']
                try:
                    map_server.publish(token, roomData)
                except IceGauntlet.Unathorized:
                    print('[ERROR] El token es inválido, no está registrado en el servidor de autenticación.')
                    return -1
                except IceGauntlet.RoomAlreadyExists:
                    print('[ERROR] Ya existe un mapa con este nombre que pertenece a otro usuario.')
                    return -1
                
        elif option == OPTION_DELETE_MAP:
            with open(map_file, 'r', encoding='UTF-8') as mapFileHandler:
                mapDictionary = json.load(mapFileHandler)
                roomName = mapDictionary['room']
                try:
                    map_server.remove(token, roomName)
                except IceGauntlet.Unathorized:
                    print('[ERROR] El token es inválido, no está registrado en el servidor de autenticación.')
                    return -1
                except IceGauntlet.RoomNotExists:
                    print('[ERROR] No existe un mapa en el servidor con ese nombre')
                    return -1
        return 0

sys.exit(MapClient().main(sys.argv))