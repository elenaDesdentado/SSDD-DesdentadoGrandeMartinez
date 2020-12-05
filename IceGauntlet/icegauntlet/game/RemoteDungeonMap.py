import sys
import Ice
Ice.loadSlice('./IceGauntlet.ice')
# pylint: disable=E0401
# pylint: disable=C0413
import IceGauntlet
# pylint: enable=E0401
# pylint: enable=C0413
    
class RemoteDungeonMap:
    def __init__(self, game_proxy, argvs):
        self.communicator = Ice.initialize(argvs)
        self.proxy = self.communicator.stringToProxy(game_proxy)
        self.game_server = IceGauntlet.DungeonPrx.checkedCast(self.proxy)
        if not self.game_server:
            raise RuntimeError('Invalid game proxy')
    
    @property
    def next_room(self):
        try:
            return self.game_server.getRoom()
        except IceGauntlet.RoomNotExists:
            print('[ERROR] No hay ningun mapa subido actualmente')
            sys.exit(-1)

    @property
    def finished(self):
        return True
    
    def __del__(self):
        self.communicator.destroy()