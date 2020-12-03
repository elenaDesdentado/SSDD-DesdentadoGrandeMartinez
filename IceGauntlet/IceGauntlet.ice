module IceGauntlet {
   
    exception Unauthorized {};
    exception RoomNotExists {};
    exception RoomAlreadyExists {};
    exception WrongRoomFormat {};

    interface Authentication {
        string getNewToken(string user, string passHash) throws Unauthorized;
        void changePassword(string user, string currentPassHash, string newPassHash) throws Unauthorized;
        bool isValid(string token);
    };

    interface Dungeon {
	    string getRoom() throws RoomNotExists; 
    };

    interface RoomManager {
        void publish(string token, string roomData) throws Unauthorized, RoomAlreadyExists, WrongRoomFormat;
        void remove(string token, string roomName) throws Unauthorized, RoomNotExists; 
    };

};