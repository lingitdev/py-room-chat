import json
import uuid
from datetime import datetime
from config import PROTOCOL_VERSION

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
