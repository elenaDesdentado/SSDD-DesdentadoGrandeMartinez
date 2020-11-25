#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import getpass
import hashlib
import Ice
Ice.loadSlice('IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413

OPTION_NEW_TOKEN = 'newtoken'
OPTION_CHANGE_PASSWORD = 'changepassword'

# ¿Queda aqui bien la comprobacion de los argumentos?
if len(sys.argv) != 3:
    print('Usage: ./auth_client <auth_client_proxy> <option>, <option> can be {0} or {1}'.format(OPTION_NEW_TOKEN, OPTION_CHANGE_PASSWORD))
    sys.exit(-1)
    
class AuthClient(Ice.Application):
    def run(self, argv):
        proxy = self.communicator().stringToProxy(argv[1])  # auth_server proxy
        print(argv[1])
        auth_server = IceGauntlet.AuthenticationPrx.checkedCast(proxy)

        if not auth_server:
            raise RuntimeError('Invalid proxy')
        
        user = input('Introduce el nombre de usuario: ')
        passwordHash = hashlib.sha256(bytes(getpass.getpass('Introduce tu contraseña: '), encoding='UTF-8')).hexdigest()
        
        if sys.argv[2].lower() == OPTION_NEW_TOKEN:
            try:
                auth_server.getNewToken(user, passwordHash)
            except IceGauntlet.Unauthorized:
                print('[ERROR] Usuario incorrecto.')
                return -1
                
        elif sys.argv[2].lower() == OPTION_CHANGE_PASSWORD:
            try:
                newPasswordHash = hashlib.sha256(bytes(getpass.getpass('Introduce tu nueva contraseña: '), encoding='UTF-8')).hexdigest()
                auth_server.changePassword(user, passwordHash, newPasswordHash)
            except IceGauntlet.Unauthorized:
                print("[ERROR] Usuario y/o contraseña incorrectos, no se ha podido cambiar la contraseña.")
                return -1
        return 0


sys.exit(AuthClient().main(sys.argv))