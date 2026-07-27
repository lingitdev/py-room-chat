💬 Py-Room-Chat

A lightweight, multi-threaded TCP socket chat server and client application built in Python using native socket and threading libraries.

This project demonstrates low-level network programming, concurrent connection handling, thread-safe message broadcasting, and room-based access control.
🌟 Key Features

    Room Management: Dynamic creation of individual chat rooms with custom IDs.

    Password Protection: Room-level password authentication for private room access.

    Multi-threading: Non-blocking architecture handling multiple client connections simultaneously.

    Thread Safety: Implements threading.Lock() to prevent race conditions during state mutation and broadcasting.

    Console UI Refresher: Clean terminal output rendering on the client side using ANSI escape codes.

    Automated Logging: Saves activity logs for the server and isolated chat histories per room in the logs/ directory.

📁 Repository Structure
Plaintext

py-room-chat/
├── README.md
├── LICENSE
└── src/
    ├── server.py
    └── client.py

🚀 Getting Started
Prerequisites

    Python 3.8 or higher installed on your machine.

    No external third-party dependencies required (uses built-in Python standard libraries).

Running the Server

    Open your terminal and navigate to the project root directory.

    Run the server script:
    Bash

    python src/server.py

The server listens on 0.0.0.0:40000 by default.
Running the Client

    By default, the client is configured to connect to 127.0.0.1 (localhost). If you are running the server on a separate device across your local network (LAN), update the SERVER_IP variable inside src/client.py.

    Launch the client application:
    Bash

    python src/client.py

    Follow the on-screen prompts to enter your nickname, room ID, and password.

🔒 Protocol & Handshake Flow

    Note: Communication runs over plain raw TCP sockets intended for local/educational testing. Traffic is currently unencrypted.

    Authentication: Client sends a fixed 16-byte nickname to the server.

    Room Request: Client sends room ID (16 bytes) and password (16 bytes).

    Validation:

        If the room exists and the password matches → Connection is granted (OK).

        If the room does not exist → Server responds with NO. The client can choose to issue a create signal (CRT) to spin up a new room dynamically.

    Chat Loop: Once connected, messages are broadcasted to all other active members in the room in real time.

📜 Commands (Client Side)

    /exit, /quit, or /q — Safely disconnect from the chat room and terminate the client session.

🚧 Upcoming Updates & Roadmap

    [ ] CLI Configuration: Pass target IP address and port via command-line arguments instead of hardcoded variables.

    [ ] Byte-Level Padding Fix: Transition from string formatting to byte-array padding to safely support multi-byte UTF-8 characters.

    [ ] Enhanced Status Codes: Granular error handling (WRONG_PASS vs NOT_FOUND) during authentication.

    [ ] TLS/SSL Encryption: Add secure socket wrapping for encrypted client-server traffic.

🧾 Ownership

This project is maintained by lingitdev and protected under GPLv3 License.
