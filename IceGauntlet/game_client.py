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
if len(sys.argv) != 2:
    print('Usage: ./game_client.py <game_server_proxy>')
    sys.exit(-1)
    
class GameClient(Ice.Application):
    def run(self, argv):
        proxy = self.communicator().stringToProxy(argv[1])  # map_server proxy
        
        game_server = IceGauntlet.AuthenticationPrx.checkedCast(proxy)

        if not game_server:
            raise RuntimeError('Invalid proxy')
        
        ## Recibir mapa como JSON o como data?

sys.exit(GameClient().main(sys.argv))