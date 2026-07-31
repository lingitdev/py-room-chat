# 💬 Py-Room-Chat `v2.0.0`

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![License](https://img.shields.io/badge/license-GPLv3-green.svg)

> 🚀 **v2.0.0 Major Update:** The project has undergone a complete architectural overhaul—moving away from raw fixed-byte text buffers to a robust, structured **JSON-based Application Layer Protocol** with full support for Direct Messaging (DM), granular status codes, dynamic room creation, and atomic thread locking.

A lightweight, multi-threaded TCP socket chat server and client application built in Python using native `socket`, `threading`, and `json` libraries.

---

## 🌟 Key Features

* **JSON Protocol Standard (v2.0):** Dynamic payload framing with newline (`\n`) packet boundaries.
* **Room Management:** Join existing rooms or create new ones dynamically with password protection.
* **Direct Messaging (DM):** Send targeted private messages to specific connected users using `@username`.
* **Multi-threading & Thread Safety:** Concurrent connection handling using `threading.Thread` paired with `threading.Lock()` to ensure atomic state updates and safe broadcasting.
* **CLI Terminal Refresher:** Dynamic, non-blocking UI updating in the terminal using ANSI escape sequences (`\r\033[K`).
* **Automated Logging:** Saves central server events to `logs/server.log` and isolated room chat histories to `logs/room_<id>.txt`.

---

## 📁 Repository Structure

* **py-room-chat/**
  * **docs/**
    * `protocol.md`
  * **src/**
    * `client`
    * `server`
  * `.gitignore`
  * `LICENSE`
  * `README.md`

---

## 🚀 Getting Started

### Prerequisites
* Python 3.8 or higher.
* No external third-party dependencies required (uses standard library modules).

### Running the Server

1. Open your terminal and navigate to the project directory.
2. Start the server:
   ```bash
   python src/server.py

The server binds to 0.0.0.0:40000 by default.
Running the Client

    Ensure the SERVER_IP inside src/client.py matches your server's IP address (use 127.0.0.1 for local testing).

    Launch the client application:
    Bash

    python src/client.py

    Enter your nickname, target Room ID, and Room Password when prompted.

🔒 Protocol Overview

Communication runs over plain TCP sockets using JSON packets terminated with a newline (\n) character delimiter.

For full specifications on packet headers, error codes, and message types, refer to the Protocol Documentation.
Quick Packet Example
JSON

{
  "msg-id": "msg-a1b2c3d4",
  "type": "JN",
  "fr": "alice",
  "to": "SRV",
  "pl": "alice@room1@pass123",
  "v": 2.0
}

📜 Commands (Client Side)

    @username <message> — Send a Direct Message (DM) to a specific active user.

    /leave or /room-out — Leave the current room without closing the application.

    /q, /exit, or /quit — Gracefully disconnect from the server and terminate the client session.

🚧 Roadmap

    [x] v2.0 Architecture: JSON-based dynamic payload architecture.

    [x] Granular status codes (401 WRONG_PASSWORD, 404 ROOM_NOT_FOUND, 409 NICKNAME_IN_USE).

    [x] Direct messaging (DM) implementation.

    [ ] CLI Arguments: Pass target IP/port via --ip and --port arguments instead of hardcoded constants.

    [ ] TLS/SSL Encryption: Secure socket wrapping via Python's ssl module for encrypted transport layer security.

🧾 License & Ownership

Maintained by lingitdev. Protected under the GPLv3 License.
