module IceGauntlet {
   
    exception Unauthorized {};
    exception RoomNotExists {};
    exception RoomAlreadyExists {};

    interface Authentication {
        string getNewToken(string user, string passHash) throws Unauthorized;
        void changePassword(string user, string currentPassHash, string newPassHash) throws Unauthorized;
        bool isValid(string token);
    };

    interface GameService {
	    string getRoom() throws RoomNotExists; 
    };

    interface MapService {
        void publish(string token, string roomData) throws Unauthorized, RoomAlreadyExists;
        void remove(string token, string roomName) throws Unauthorized, RoomNotExists; 
    };

};