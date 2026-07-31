import socket
import threading
import json
import config
from protocol import send_packet
from sender import send_messages

def main():
    while True:
        config.client_nickname = input("Enter your nickname: ").strip()
        
        if not config.client_nickname:
            print("Nickname cannot be empty! Please enter a valid nickname.\n")
        elif "@" in config.client_nickname or " " in config.client_nickname:
            print("Nickname cannot contain spaces or '@' character!\n")
        else:
            break

    while True: 
        room_id = input("Enter Room ID to join: ").strip()
        room_pass = input(f"Enter password for Room '{room_id}': ").strip()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((config.SERVER_IP, config.SERVER_PORT))
        except Exception as e:
            print(f"Connection failed: {e}")
            return

        send_packet(client_socket, "JN", f"{config.client_nickname}@{room_id}@{room_pass}", "SRV")

        buffer = ""
        while "\n" not in buffer:
            chunk = client_socket.recv(config.BUFFER_SIZE).decode('utf-8', errors='ignore')
            if not chunk:
                print("Server disconnected during handshake.")
                return
            buffer += chunk

        line, buffer = buffer.split("\n", 1)
        data = json.loads(line)

        is_connected_to_room = False

        if data["type"] == "ACK":
            is_connected_to_room = True
            
        elif data["type"] == "ERR":
            error_code = data.get("pl", "")
            print(f"Server Error: {error_code}")
            
            if "404" in error_code or "NOT_FOUND" in error_code:
                decision = input(f"Room '{room_id}' not found. Would you like to create it? (y/n): ")
                if decision.lower() == 'y':
                    send_packet(client_socket, "CRT", f"{config.client_nickname}@{room_id}@{room_pass}", "SRV")
                    
                    while "\n" not in buffer:
                        chunk = client_socket.recv(config.BUFFER_SIZE).decode('utf-8', errors='ignore')
                        if not chunk:
                            print("Server disconnected during room creation.")
                            return
                        buffer += chunk
                        
                    line, buffer = buffer.split("\n", 1)
                    crt_data = json.loads(line)
                    
                    if crt_data["type"] == "ACK":
                        is_connected_to_room = True
                    else:
                        print(f"Room creation failed: {crt_data.get('pl')}")
                        client_socket.close()
                        return
                else:
                    send_packet(client_socket, "DISC", "", "SRV")
                    client_socket.close()
                    return

            elif "401" in error_code or "WRONG_PASSWORD" in error_code:
                pass_true = False
                while not pass_true:
                    room_pass = input(f"Enter password for Room '{room_id}': ").strip()
                    
                    if room_pass in ['/q', '/out']:
                        client_socket.close()
                        break

                    send_packet(client_socket, "JN", f"{config.client_nickname}@{room_id}@{room_pass}", "SRV")

                    while "\n" not in buffer:
                        chunk = client_socket.recv(config.BUFFER_SIZE).decode('utf-8', errors='ignore')
                        if not chunk:
                            print("Server disconnected during handshake.")
                            return
                        buffer += chunk
                    
                    line, buffer = buffer.split("\n", 1)
                    data = json.loads(line)

                    if data['type'] == "ACK":
                        pass_true = True
                        is_connected_to_room = True 
                        
            else:
                client_socket.close()
                return

        if is_connected_to_room:
            print(f"--- Successfully joined room: {room_id} ---")
            input_thread = threading.Thread(target=send_messages, args=(client_socket,), daemon=True)
            input_thread.start()
            break

    while True:
        try:
            while "\n" not in buffer:
                chunk = client_socket.recv(config.BUFFER_SIZE).decode('utf-8', errors='ignore')
                if not chunk:
                    print("\r\033[K\nServer disconnected.")
                    break
                buffer += chunk
                
            if not buffer:
                break

            line, buffer = buffer.split("\n", 1)
            message = json.loads(line)
                
            msg_type = message.get("type")
            if msg_type == "MSG":
                sender = message.get("fr", "Unknown")
                content = message.get("pl", "")
                print(f"\r\033[K{sender}: {content}\n{config.client_nickname}: ", end="", flush=True)
            elif msg_type == "SYS":
                print(f"\r\033[K[SYS] {message.get('pl')}\n{config.client_nickname}: ", end="", flush=True)
            elif msg_type == "DM":
                sender = message.get("fr", "Unknown")
                content = message.get("pl", "")
                print(f"\r\033[K[DM - {sender}]: {content}\n{config.client_nickname}: ", end="", flush=True)
                    
        except Exception:
            print("\r\033[K\nConnection error occurred.")
            break

if __name__ == "__main__":
    main()
