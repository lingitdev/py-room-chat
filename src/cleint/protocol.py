import json
import uuid
import config

def build_packet(msg_type: str, payload: str, to: str = "SRV") -> str:
    raw_packet = {
        "msg-id": f"msg-{uuid.uuid4().hex[:8]}",
        "type": msg_type,
        "to": to,
        "pl": payload,
        "v": config.PROTOCOL_VERSION
    }
    packet = {key: value for key, value in raw_packet.items() if value is not None}
    return json.dumps(packet, ensure_ascii=False) + "\n"

def send_packet(sock, msg_type, payload="", to="SRV"):
    sock.sendall(build_packet(msg_type, payload, to).encode("utf-8"))
