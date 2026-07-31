import socket
import json
import threading
from config import BUFFERSIZE, SERVER_PORT, lock, active_clients
from protocol import send_packet
from models import create_room, find_room, WrongPasswordError

def join_a_room(conn, room_information):
    try:
        nickname, room_id, room_pass = [x.strip() for x in room_information.split("@")]
    except ValueError:
        send_packet(conn, "ERR", "400 INVALID_PACKET", "SRV")
        return None, None

    if not nickname:
        send_packet(conn, "ERR", "400 INVALID_NICKNAME", "SRV")
        return None, None

    try:
        room = find_room(room_id, room_pass)

        if room is not None:
            with lock:
                if nickname in room.members:
                    send_packet(conn, "ERR", "409 NICKNAME_ALREADY_IN_USE", "SRV")
                    return None, None

            room.add_member(nickname, conn)
            send_packet(conn, "ACK", "200 OK", "SRV")
            return room, nickname
        else:
            send_packet(conn, "ERR", "404 ROOM_NOT_FOUND", "SRV")
            return None, None
        
    except WrongPasswordError:
        send_packet(conn, "ERR", "401 WRONG_PASSWORD", "SRV")
        return None, None

def client_handler(connection: socket.socket):
    nickname: str = None
    current_room: object = None
    buffer = ""
    while True:
        while "\n" not in buffer:
            try:
                chunk = connection.recv(BUFFERSIZE).decode("utf-8", errors="ignore")
            except (ConnectionResetError, OSError):
                if current_room and nickname:
                    current_room.remove_member(nickname, connection)
                with lock:
                    active_clients.pop(nickname, None)
                return

            if not chunk:
                if current_room is not None:
                    current_room.remove_member(nickname, connection)
                    return
                else:
                    print("Server disconnected during handshake.")
                    return
            buffer += chunk

        line, buffer = buffer.split("\n", 1)
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            send_packet(connection, "ERR", "400 INVALID_JSON", "SRV")
            continue

        if data.get('type') and data['type'] != "":
            if data['type'] == "JN":
                if data.get('pl') and data['pl'] != "":
                    current_room, nickname = join_a_room(connection, data['pl'])
                    if nickname:
                        with lock:
                            active_clients[nickname] = connection

            elif data['type'] == "DISC":
                if current_room and nickname:
                    current_room.remove_member(nickname, connection)

                connection.close()

                with lock:
                    active_clients.pop(nickname, None)
                break
                    
            elif data['type'] == "MSG":
                if current_room and nickname:
                    if not data["pl"].strip():
                        send_packet(connection, "ERR", "400 EMPTY_MESSAGE", "SRV")
                        continue

                    current_room.broadcast(nickname, connection, data["pl"])
                else:
                    send_packet(connection, "ERR", "400 NOT_IN_A_ROOM", "SRV")

            elif data['type'] == "QT":
                if current_room and nickname:
                    current_room.remove_member(nickname, connection)
                    current_room = None
                    send_packet(connection, "ACK", "200 LEFT_ROOM", "SRV")
                    with lock:
                        if nickname in active_clients:
                            del active_clients[nickname] 
                else:
                    send_packet(connection, "ERR", "400 NOT_IN_A_ROOM", "SRV")

            elif data['type'] == "PING":
                send_packet(connection, "PONG", "PONG", "SRV")

            elif data['type'] == "CRT":
                try:
                    nickname, room_id, room_pass = [x.strip() for x in data['pl'].split("@")]
                except ValueError:
                    send_packet(connection, "ERR", "400 INVALID_PACKET", "SRV")
                    continue

                new_room = create_room(room_id, nickname, room_pass, {})
                new_room.add_member(nickname, connection)
                current_room = new_room
                send_packet(connection, "ACK", "200 CREATE_ROOM", "SRV")
                with lock:
                    active_clients[nickname] = connection

            elif data['type'] == "DM":
                target_nickname = data.get('to')
                
                if not nickname:
                    send_packet(connection, "ERR", "400 NOT_LOGGED_IN", "SRV")
                    continue

                if not data["pl"].strip():
                    send_packet(connection, "ERR", "400 EMPTY_MESSAGE", "SRV")
                    continue

                with lock:
                    target_conn = active_clients.get(target_nickname)

                    if target_conn:
                        send_packet(target_conn, "DM", data["pl"], to=target_nickname, fr=nickname)
                        send_packet(connection, "ACK", "200 DM_SENT", "SRV")

                    else:
                        send_packet(connection, "ERR", "404 USER_NOT_FOUND", "SRV")

def main():
    create_room("MAIN", "", "", {})

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', SERVER_PORT))
    server_socket.listen()

    print("Server Started")
    print("Listening for incoming connections...")

    while True:
        connection, addr = server_socket.accept()
        handler_thread = threading.Thread(target=client_handler, args=(connection,))
        handler_thread.daemon = True
        handler_thread.start()

if __name__ == "__main__":
    main()
