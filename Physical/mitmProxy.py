#!/usr/bin/env python3
import asyncio
import argparse
import random
from collections import deque

# To run the proxy, run the following:
# python mitmProxy.py --listen 4000 --remote <ser2net_ip>:<ser2net_port>
# connect to localhost:4000 on PanelPro


# A little circular buffer of the last N messages for replaying
REPLAY_BUFFER = deque(maxlen=100)

# default assignments, global declarations
remote_host = "localhost"
remote_port = 5000

def should_drop(data: bytes) -> bool:
    """
    Return True if you want to *drop* this frame instead of forwarding.
    E.g. random drop of 10%:
    """
    return random.random() < 0.1

def should_replay(data: bytes) -> bool:
    """
    Return True if you want to *replay* an earlier frame before forwarding this one.
    E.g. on 5% of frames:
    """
    return random.random() < 0.05

def pick_replay() -> bytes:
    """
    Choose one of the buffered frames to replay.
    """
    if not REPLAY_BUFFER:
        return b''
    return random.choice(REPLAY_BUFFER)

async def forward(reader: asyncio.StreamReader,
                  writer: asyncio.StreamWriter,
                  direction: str):
    """
    Copy from reader→writer, applying drop/replay logic.
    direction is for logging only: "C→S" or "S→C".
    """
    peer = writer.get_extra_info('peername')
    while True:
        data = await reader.read(4096)
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        # 1) Optionally drop
        if should_drop(data):
            print(f"[DROP {direction}] {data!r}")
            continue

        # 2) Optionally replay an earlier message
        if should_replay(data):
            replay = pick_replay()
            if replay:
                print(f"[REPLAY {direction}] {replay!r}")
                writer.write(replay)
                await writer.drain()

        # 3) Forward the real data
        print(f"[FORWARD {direction}] {data!r}")
        writer.write(data)
        await writer.drain()

        # 4) Buffer it for potential future replay
        REPLAY_BUFFER.append(data)

async def handle_client(local_reader, local_writer):
    # Connect to the real server
    try:
        remote_reader, remote_writer = await asyncio.open_connection(remote_host, remote_port)
    except Exception as e:
        print("Could not connect to remote:", e)
        local_writer.close()
        await local_writer.wait_closed()
        return

    # Launch bidirectional forwarding
    await asyncio.gather(
        forward(local_reader,  remote_writer, "C→S"),
        forward(remote_reader, local_writer,  "S→C"),
    )

def main():
    p = argparse.ArgumentParser(description="Simple TCP MITM proxy with drop/replay hooks")
    p.add_argument("--listen",   type=int, required=True, help="Local port to listen on")
    p.add_argument("--remote",   required=True,   help="Remote host:port to connect to")
    args = p.parse_args()

    remote_host, remote_port = args.remote.split(":")
    remote_port = int(remote_port)

    loop = asyncio.get_event_loop()
    server = asyncio.start_server(handle_client, "0.0.0.0", args.listen)

    srv = loop.run_until_complete(server)
    print(f"Proxy listening on {srv.sockets[0].getsockname()} → forwarding to {remote_host}:{remote_port}")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.close()
        loop.run_until_complete(srv.wait_closed())

if __name__ == "__main__":
    main()
