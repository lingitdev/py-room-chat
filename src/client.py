import socket
import threading
import os

SERVER_IP: str = '192.168.1.102'
SERVER_PORT: int = 40000
BUFFER_SIZE: int = 1024

client_nickname: str = ""


def send_messages(client_socket: socket.socket):
    global client_nickname
    while True:
        try:
            message = input(f"{client_nickname}: ")
            if not message.strip():
                print("Cannot send an empty message. Please type something.")
                continue

            if message.strip().lower() in ['/q', '/exit', '/quit']:
                print("\nLeaving the chat...")
                client_socket.close()
                os._exit(0)

            formatted_message = f"{client_nickname}: {message}"
            client_socket.sendall(formatted_message.encode('utf-8'))
        except Exception:
            print("\nError sending message.")
            break


def main():
    global client_nickname

    client_nickname = input("Enter your nickname: ").strip()
    nickname_bytes = client_nickname.ljust(16)[:16].encode('utf-8')

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
    except Exception as e:
        print(f"Could not connect to server at {SERVER_IP}:{SERVER_PORT} - {e}")
        return

    client_socket.sendall(nickname_bytes)

    print("Waiting for server approval...")
    response = client_socket.recv(4).decode('utf-8', errors='ignore').strip()

    if response == "OK":
        print("Connected to server!")
        
        room_id = input("Enter Room ID to join: ").strip()
        room_id_bytes = room_id.ljust(16)[:16].encode('utf-8')
        client_socket.sendall(room_id_bytes)

        room_pass = input(f"Enter password for Room '{room_id}': ").strip()
        room_pass_bytes = room_pass.ljust(16)[:16].encode('utf-8')
        client_socket.sendall(room_pass_bytes)

        data = client_socket.recv(BUFFER_SIZE).decode('utf-8', errors='ignore').strip()
        is_connected_to_room = False

        if data == "OK":
            is_connected_to_room = True
        elif data == "NO":
            decision = input(f"Room '{room_id}' not found. Would you like to create it? (y/n): ")
            if decision.lower() == 'y':
                client_socket.sendall(b"CRT")
                is_connected_to_room = True
            else:
                client_socket.sendall(b"CANCEL")
                client_socket.close()
                return

        if is_connected_to_room:
            print(f"--- Successfully joined room: {room_id} ---")
            
            # Start thread for sending user input
            input_thread = threading.Thread(target=send_messages, args=(client_socket,), daemon=True)
            input_thread.start()

            # Main thread listens for incoming messages
            while True:
                try:
                    incoming_data = client_socket.recv(BUFFER_SIZE)
                    if not incoming_data:
                        print("\r\033[K\nServer disconnected.")
                        break
                    
                    message = incoming_data.decode('utf-8', errors='ignore')
                    print(f"\r\033[K{message}\n{client_nickname}: ", end="", flush=True)
                except Exception:
                    print("\r\033[K\nConnection error occurred.")
                    break
    else:
        print("Server rejected connection.")
        client_socket.close()


if __name__ == "__main__":
    main()
