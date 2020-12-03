#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import argparse
import Ice
Ice.loadSlice('IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413

OPTION_PUBLISH_MAP = 'publishmap'
OPTION_DELETE_MAP = 'deletemap'


def parse_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument("MapServerProxy", help="Proxy del servidor de mapas para interactuar con el mismo")
    parser.add_argument("token", help="Token de usuario para comprobar su legitimidad e interacturas con el servidor de mapas")
    parser.add_argument("map", help="Mapa proporcionado para poder jugarlo")
    parser.add_argument("-o", "--operation", help="Operación que ejecutará el servidor de autenticación", choices=[OPTION_PUBLISH_MAP, OPTION_DELETE_MAP])
    args = parser.parse_args()
    return args

class MapClient(Ice.Application):
    def run(self, argv):
        options = parse_commandline()
        
        proxy = self.communicator().stringToProxy(options.MapServerProxy) 
        token = options.token
        map_file = options.map
        
        map_server = IceGauntlet.RoomManagerPrx.checkedCast(proxy)

        if not map_server:
            raise RuntimeError('Invalid map server proxy')
        
        if options.operation.lower() == OPTION_PUBLISH_MAP:
            with open(map_file, 'r', encoding='UTF-8') as mapFileHandler:
                roomData = mapFileHandler.read() 
                try:
                    map_server.publish(token, roomData)
                except IceGauntlet.Unauthorized:
                    print('[ERROR] El token es inválido, no está registrado en el servidor de autenticación.')
                    return -1
                except IceGauntlet.RoomAlreadyExists:
                    print('[ERROR] Ya existe un mapa con este nombre que pertenece a otro usuario.')
                    return -1
                except IceGauntlet.WrongRoomFormat:
                    print('[ERROR] El mapa en formato JSON no se ajusta al formato necesario para poder ser jugado (no tiene nombre o datos)')
                    return -1
                    
        elif options.operation.lower() == OPTION_DELETE_MAP:
            with open(map_file, 'r', encoding='UTF-8') as mapFileHandler:
                mapDictionary = json.load(mapFileHandler)
                roomName = mapDictionary['room']
                try:
                    map_server.remove(token, roomName)
                except IceGauntlet.Unauthorized:
                    print('[ERROR] El token es inválido, no está registrado en el servidor de autenticación o el mapa es de otro usuario.')
                    return -1
                except IceGauntlet.RoomNotExists:
                    print('[ERROR] No existe un mapa en el servidor con ese nombre.')
                    return -1
        else:
            print('[ERROR] Las opciones que puedes usar con -o: {0} o {1}'.format(OPTION_PUBLISH_MAP, OPTION_DELETE_MAP))
            return -1
                
        print('[SUCCESS] Operación realizada con éxito.')
        return 0

sys.exit(MapClient().main(sys.argv))