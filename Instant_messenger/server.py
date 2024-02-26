import socket
import threading
import os
import sys
import logging


HEADER = 64 # size of header = 64 bytes
PORT = int(sys.argv[1]) #get port num from terminal
SERVER = socket.gethostbyname(socket.gethostname())  #IP addr of server
ADDR = (SERVER, PORT)
FORMAT = 'utf-8' #encoding format
DISCONNECT_MESSAGE = "!DISCONNECT"
HOSTNAME = 'localhost'
DOWNLOAD_DIR = './downloads'
LISTFILE_MSG = '!LISTFILES'
DOWNLOAD_MSG = '!DOWNLOAD'

# logging library
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG) #config logging
logger = logging.getLogger(__name__) #create logger object

# file handling
file_handler = logging.FileHandler('server.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOSTNAME, PORT))
server.listen()

# store client info
clients = []
usernames = []
curr_connections = {} #dict of curr connections

##### functions #####

def list_files():
    files = os.listdir(DOWNLOAD_DIR)
    logger.info(f"Listing files: {files}")
    return files

def send_file(client, file_name):
    file_path = os.path.join(DOWNLOAD_DIR, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            data = file.read(1024)
            while data:
                client.send(data)
                data = file.read(1024)
        client.send("EOF".encode(FORMAT))
    else:
        client.send("File not found".encode(FORMAT))

def unicast(client, recipient_username, msg):
    for target_client, details in curr_connections.items():
        if details['username'] == recipient_username:
            try:
                target_client.send(msg.encode(FORMAT))
                return True
            except:
                return False
    return False


# broadcast msg to clients
def msg_broadcast(sender, msg):
   for client in clients:
       if client is None or client != sender:
           client.send(msg.encode(FORMAT))

# handle client connections
def handle_client(client, client_addr, parent_dir):
    global curr_connections, clients  
    username = curr_connections.get(client, {}).get('username', 'Unknown')
    
    while True:
        try:
            decoded_msg = client.recv(1024).decode(FORMAT)
                
            if decoded_msg == DISCONNECT_MESSAGE:
                msg_broadcast(client, f'{username} left chat \n')
                logger.info(f'{username} {client_addr} left server \n')

                # remove client 
                clients.remove(client)
                del curr_connections[client]
                client.close()
                break

            # download function
            elif decoded_msg == LISTFILE_MSG:
                files = list_files()
                file_list = '\n'.join(files)
                client.send(file_list.encode(FORMAT))
            elif decoded_msg.startswith(DOWNLOAD_MSG):
                file_name = decoded_msg.split()[1]
                send_file(client, file_name)

            else:
                # Broadcast message
                if decoded_msg.startswith("[") and "]" in decoded_msg:
                    end_index = decoded_msg.find("]")
                    recipient_username = decoded_msg[1:end_index]
                    message_content = decoded_msg[end_index + 2:]
                    sent = False
                    for recipient_client, details in curr_connections.items():
                        if details['username'] == recipient_username:
                            recipient_client.send(f'{username}: {message_content}'.encode(FORMAT))
                            sent = True
                    if not sent:
                        client.send(f'user {recipient_username} not found'.encode(FORMAT))
                else:
                    msg_broadcast(client, f'{username}: {decoded_msg}')

        except ConnectionResetError as e:
            logger.info(f'{username} {client_addr} disconnected: {e}')
            msg_broadcast(client, f'{username} left chat \n')
            if client in clients:
                clients.remove(client)
            if client in curr_connections:
                del curr_connections[client]
            break
        except Exception as exemption:
            logger.error(f'error for {username} {exemption}')
            
            if client in clients:
                clients.remove(client)
            if client in curr_connections:
                del curr_connections[client]
            break

            
            

# handle new clients
def start():
   global curr_connections, clients #make dict globally accessible
   while True:
       print('[WAITING] waiting for connection...')
       client, client_addr= server.accept()
       username = client.recv(1024).decode(FORMAT)
       
       curr_connections[client] = {'username': username, 'address': client_addr}  #append dict
       clients.append(client)
       print(f'client has joined. Username:{username}, IP Address and Port Number: {client_addr}')
       
       #broadcast that new client joined server
       msg_broadcast(None, f'{username} at {client_addr} has joined \n')
       logger.info(f'{username} has joined server from {client_addr} \n')

       #sends messages to client
       client.send('\n You have connected to server \n'.encode(FORMAT))
       client.send('\n Type a message. Type "!DISCONNECT" to exit'.encode(FORMAT))
       
       #gets curr dir of server
       parent_dir = os.getcwd() 
       path = os.path.join(parent_dir, username) #set the clients path

       #start thread for client
       thread = threading.Thread(target=handle_client, args=(client, client_addr, parent_dir))
       thread.start()

       #create folder for client
       if not os.path.exists(path):
           os.mkdir(path)
        
        

# run program
if __name__ == "__main__":
    print("[SERVER] server is starting...")
    start()





