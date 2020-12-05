#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
    Authorization client for IceGauntlet
'''

from __future__ import print_function
import sys
import getpass
import hashlib
import argparse
# pylint: disable=import-error
import Ice
# pylint: enable=import-error
Ice.loadSlice('IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
# pylint: disable=too-few-public-methods
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413

OPTION_NEW_TOKEN = 'newtoken'
OPTION_CHANGE_PASSWORD = 'changepassword'
TOKENS_FILE = 'tokens'


def parse_commandline():
    """ Parses the commandline arguments using argparse """
    parser = argparse.ArgumentParser()
    parser.add_argument("user",
                        help="Nombre de usuario registrado en el servidor de autenticación")
    parser.add_argument("AuthenticationServerProxy",
                        help="Proxy del servidor de autenticación para interactuar con el mismo")
    parser.add_argument("-o", "--operation",
                        help="Operación que ejecutará el servidor de autenticación",
                        choices=[OPTION_NEW_TOKEN, OPTION_CHANGE_PASSWORD])
    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(-1)
    return args

class AuthClient(Ice.Application):
    '''
        Class in charge of interacting with the auth server in order to
        implement the behaviour of the client
    '''
    def __init(self):
        """ Empty constructor """
        pass

    def run(self, argv):
        """ Implementation of the superclass method for executing the application """
        options = parse_commandline()

        proxy = self.communicator().stringToProxy(
            options.AuthenticationServerProxy)  # auth_server proxy
        print(argv[1])
        auth_server = IceGauntlet.AuthenticationPrx.checkedCast(proxy)

        if not auth_server:
            raise RuntimeError('Invalid proxy')

        password_input = getpass.getpass('Introduce tu password: ')
        password_hash = None if password_input == '' else hashlib.sha256(
            bytes(password_input, encoding='UTF-8')).hexdigest()

        if options.operation.lower() == OPTION_NEW_TOKEN:
            try:
                with open(TOKENS_FILE, 'w', encoding='UTF-8') as file_handler:
                    new_token = auth_server.getNewToken(options.user, password_hash)
                    file_handler.write(new_token+'\n')
            except IceGauntlet.Unauthorized:
                print('[ERROR] Usuario incorrecto.')
                return -1

        elif options.operation.lower() == OPTION_CHANGE_PASSWORD:
            try:
                new_password_hash = hashlib.sha256(bytes(getpass.getpass(
                    'Introduce tu nueva contraseña: '), encoding='UTF-8')).hexdigest()
                auth_server.changePassword(options.user, password_hash, new_password_hash)
            except IceGauntlet.Unauthorized:
                print(
                    "[ERROR] Usuario y/o contraseña incorrectos, no se ha " +
                    "podido cambiar la contraseña.")
                return -1
        else:
            print('[ERROR] Las opciones que puedes usar con -o: {0} o {1}'.format(
                OPTION_NEW_TOKEN, OPTION_CHANGE_PASSWORD))
            return -1

        print('[SUCCESS] Operación realizada con éxito.')
        return 0


sys.exit(AuthClient().main(sys.argv))