import time
import zmq
import msgpack

# Connect to the Matrix Listener
context = zmq.Context()
sender = context.socket(zmq.PUSH)
sender.connect("tcp://127.0.0.1:5555")

print("\n[+] BOOTING OMNI-AI MARITIME MEMBRANE BRIDGE")

raw_vessel_telemetry = {
    "lat": 52.4420,  # Zaandam Area
    "lon": 4.8292,
    "sog_knots": 4.2,
    "cog_deg": 185.0,
    "gps_sat_lock": 9 
}

def transmit_to_sigma_bus(telemetry):
    v_state = [telemetry["lat"], telemetry["lon"], telemetry["sog_knots"], telemetry["cog_deg"]]
    
    # ASSEMBLE M-PROTOCOL PACKAGE
    m_message = {
        "v": v_state,
        "sigma": {"type": "gaussian", "params": {"variance": [0.1, 0.1, 0.5, 2.0]}},
        "pi": [{"node_id": "GPS_NMEA_0183_RAW", "timestamp": time.time(), "confidence": 0.9}],
        "delta": "MARITIME_NAV",      
        "kappa": 0.95 if telemetry["gps_sat_lock"] > 8 else 0.40,
        "tau": int(time.time() * 1000),
        "mu": "WAKE"                  
    }

    # Binary Serialization via MessagePack for zero latency over the wire
    payload = msgpack.packb(m_message, use_bin_type=True)

    print("[<-] Encapsulated in MsgPack. Firing over ZMQ ΣBUS to Cognitive Matrix...")
    sender.send(payload)
    print("[✓] Sent.\n")

if __name__ == "__main__":
    time.sleep(1)
    transmit_to_sigma_bus(raw_vessel_telemetry)
