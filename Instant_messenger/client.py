import socket
import threading
import os 
import sys



HEADER = 64 # size of header = 64 bytes
PORT = int(sys.argv[3])
USERNAME = sys.argv[1]
HOSTNAME = sys.argv[2]
FORMAT = 'utf-8' #encoding format
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDR = (HOSTNAME, PORT)
LISTFILE_MSG = '!LISTFILES'
DOWNLOAD_MSG = '!DOWNLOAD'
DOWNLOAD_DIR = './downloads'


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #initialise socket
client.connect(ADDR) #connect

def send():
   while True:
       msg = input("Enter your message: ")
       if msg == DISCONNECT_MESSAGE:
           client.send(DISCONNECT_MESSAGE.encode(FORMAT))
           client.close()
           break
       if msg == LISTFILE_MSG:
           client.send(msg.encode(FORMAT))
           file_list = client.recv(4096).decode(FORMAT)
           print("files available:\n" + file_list)
       elif msg.startswith(DOWNLOAD_MSG):
        client.send(msg.encode(FORMAT))
        file_name = msg.split()[1]
        with open(os.path.join(DOWNLOAD_DIR, file_name), 'wb') as file:
            while True:
                file_data = client.recv(1024)
                if file_data.decode(FORMAT) == "EOF":
                    print(f'{file_name} download complete')
                    break
                elif file_data.decode(FORMAT) == "File not found":
                    print("File not found")
                    break
                else:
                    file.write(file_data)

       else:
           client.send(f'{USERNAME}: {msg}'.encode(FORMAT))


def recv():
    while True:
        try:
            msg = client.recv(1024).decode(FORMAT)
            print(msg)
        except:
            print("server has ended the connection")
            client.close()
            break


send = threading.Thread(target=send)
send.start()

recv = threading.Thread(target=recv)
recv.start()