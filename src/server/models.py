import random
from datetime import datetime
from config import lock, rooms
from protocol import send_packet

class WrongPasswordError(Exception):
    pass

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
