module IceGauntlet {
   
    exception Unauthorized {};
    exception RoomNotExists {};
    exception RoomAlreadyExists {};
    exception WrongRoomFormat {};

    sequence<string> roomList;
  
    struct Actor {
        string actorId;
        string attributes;
    };

    struct Item {
        string itemId;
        int itemType;
        int positionX;
        int positionY;
    };

    sequence<Actor> cast;
    sequence<Item> objects;
    sequence<byte> bytes;

    interface Authentication {
        string getNewToken(string user, string passHash) throws Unauthorized;
        void changePassword(string user, string currentPassHash, string newPassHash) throws Unauthorized;
        string getOwner(string token) throws Unauthorized;
    };

    interface Dungeon {
	    string getRoom() throws RoomNotExists; 
    };

    interface RoomManager {
        void publish(string token, string roomData) throws Unauthorized, RoomAlreadyExists, WrongRoomFormat;
        void remove(string token, string roomName) throws Unauthorized, RoomNotExists;
        roomList availableRooms();
        string getRoom(string roomName) throws RoomNotExists;
    };

    // Event channel for Room Manager synchronization
    interface RoomManagerSync {
        void hello(RoomManager* manager, string managerId);
        void announce(RoomManager* manager, string managerId);
        void newRoom(string roomName, string managerId);
        void removedRoom(string roomName);
    };

};