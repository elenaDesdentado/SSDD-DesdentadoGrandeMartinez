#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
import json
Ice.loadSlice('IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413

MAPS_DB = "maps.json"

class MapServiceI(IceGauntlet.MapService):
    
    def __init__(self, authProxy):
        # auth_server = IceGauntlet.AuthenticationPrx.checkedCast(proxy)
        self.auth_server = IceGauntlet.AuthenticationPrx.checkedCast(authProxy)
        if not auth_server:
            raise RuntimeError('Invalid proxy')
        
    
    def publish(self, token, roomData, current=None):
        print("{0}: {1}".format(self.n, message))
        sys.stdout.flush()
        self.n += 1
        
    def remove(self, token, roomName, current=None):
        if not(auth_server.isValid(token)):
            raise IceGauntlet.Unauthorized()
        else:
            # Leer el JSON 
            if roomName not in MAPS_DB:   # Llamar a json.load()
                raise IceGauntlet.RoomNotExists()
            
        self.n += 1

class GameServiceI(IceGauntlet.GameService):
    def getRoom(self, current=None):
        print("{0}: {1}".format(self.n, message))
        sys.stdout.flush()
        self.n += 1

class Server(Ice.Application):
    
    def run(self, argv):
        broker = self.communicator()        #Luego hay que usarlo para el auth_server y conseguir el proxy
        servant = PrinterI()

        adapter = broker.createObjectAdapter("PrinterAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("printer1"))

        print(proxy, flush=True)

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


server = Server()
sys.exit(server.main(sys.argv))