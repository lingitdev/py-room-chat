import socket
import json
import uuid
from datetime import datetime
import threading
import random
import os

os.makedirs("logs", exist_ok=True)

BUFFERSIZE: int = 1024
PROTOCOL_VERSION = 1.0
SERVER_PORT = 40000

rooms = []
active_clients = {}
lock = threading.Lock()

class WrongPasswordError(Exception):
    pass

def build_packet(msg_type: str, payload: str, to: str, fr: str) -> str:
    raw_packet = {
        "msg-id": f"msg-{uuid.uuid4().hex[:8]}",
        "type": msg_type,
        "fr": fr,
        "to": to,
        "pl": payload,
        "tm": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "v": PROTOCOL_VERSION
    }
    packet = {key: value for key, value in raw_packet.items() if value is not None}
    return json.dumps(packet, ensure_ascii=False) + "\n"

def send_packet(sock, msg_type, payload="", to="SRV", fr: str = ""):
    packet_str = build_packet(msg_type, payload, to, fr)
    try:
        sock.sendall(packet_str.encode("utf-8"))
    except OSError:
        return
    date_and_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/server.log", "a", encoding="utf-8") as f:
        f.write(f"[{date_and_time}] [OUT] {packet_str}")

class Room:

    def __init__(self, room_id: str, name: str, password: str, members: dict):
        self.name = name
        self.password = password
        self.id = room_id
        self.members = members

    def add_member(self, nickname: str, conn=None):
        with lock:
            self.members[nickname] = conn
        self.broadcast("SYSTEM", conn, f"{nickname} joined.")
    
    def remove_member(self, nickname: str, conn=None):
        with lock:
            if nickname in self.members:
                del self.members[nickname]
        self.broadcast("SYSTEM", conn, f"{nickname} left.")

    def broadcast(self, sender, sender_conn, message):
        with lock:
            member_list = list(self.members.values())

        date_and_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(f"logs/room_{self.id}.txt", "a", encoding="utf-8") as f:
            f.write(f"[{date_and_time}] {sender}: {message}\n")

        for conn in member_list:
            if conn != sender_conn:
                try:
                    send_packet(conn, "MSG", payload=message, to="RM", fr=sender)
                except Exception:
                    pass

def find_room(room_id: str, room_pass: str):
    with lock:
        for room in rooms:
            if room.id == room_id and room.password == room_pass:
                return room
            elif room.id == room_id and room.password != room_pass:
                raise WrongPasswordError()
    return None

def create_room(room_id: str, room_name: str, room_pass: str, room_members: dict):
    if room_id == "":
        room_id = str(random.randint(100001, 999999))
    new_room = Room(f"{room_id}", f"{room_name}", f"{room_pass}", room_members)
    with lock:
        rooms.append(new_room)
    return new_room

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
