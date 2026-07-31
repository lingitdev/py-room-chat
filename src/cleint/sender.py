import os
import socket
import config
from protocol import send_packet

def send_messages(client_socket: socket.socket):
    while True:
        try:
            message = input(f"{config.client_nickname}: ")
            if not message.strip():
                print("Cannot send an empty message. Please type something.")
                continue

            cleaned_msg = message.strip().lower()

            if cleaned_msg in ['/leave', '/room-out']:
                print("\nLeaving the room...")
                send_packet(client_socket, "QT", "LEAVE_ROOM", "SRV")
                continue

            if cleaned_msg in ['/q', '/exit', '/quit']:
                print("\nDisconnecting from server...")
                send_packet(client_socket, "DISC", "", "SRV")
                client_socket.close()
                os._exit(0)

            if message.startswith("@"):
                parts = message.split(" ", 1)
                target_user = parts[0][1:]  

                if not target_user:
                    print("Invalid command or username.")
                    continue

                dm_payload = parts[1] if len(parts) > 1 else ""
                if not dm_payload.strip():
                    print(f"Cannot send an empty message to user ({target_user}).")
                    continue

                send_packet(client_socket, "DM", dm_payload, to=target_user)
                print(f"[DM -> {target_user}]: {dm_payload}")
                continue

            send_packet(client_socket, "MSG", message, "RM")
        except Exception:
            print("\nError sending message.")
            break
