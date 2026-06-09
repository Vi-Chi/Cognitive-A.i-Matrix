import zmq
import msgpack
import time

def matrix_listen():
    context = zmq.Context()
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://127.0.0.1:5555")

    print("\n[ΦΩ] COGNITIVE MATRIX LISTENER ONLINE.")
    print("[*] Listening on ΣBUS (Port 5555) for M-Protocol Tensors...\n")

    while True:
        try:
            # Await payload
            message_bytes = receiver.recv()
            
            # Decode the MsgPack binary
            m_protocol_data = msgpack.unpackb(message_bytes, raw=False)
            
            print(f"[{time.strftime('%H:%M:%S')}] [+] ΣBUS PAYLOAD RECEIVED")
            print(f"     Domain: {m_protocol_data['delta']}")
            print(f"     Trust (κ): {m_protocol_data['kappa']}")
            print(f"     Vector/Coords: {m_protocol_data['v']}")
            print("     -> Routing to 3-6-9 Lenses...\n")
            
        except KeyboardInterrupt:
            print("\nShutting down listener...")
            break

if __name__ == "__main__":
    matrix_listen()
