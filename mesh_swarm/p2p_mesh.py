import socket
import json
import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Callable

class AOSMeshSwarm:
    """
    Phase 4: Sovereign P2P Local Mesh (Edge Swarm).
    Enables air-gapped, zero-cloud peer discovery and compute collaboration
    across local edge nodes using UDP broadcast beacons.
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        broadcast_port: int = 50555,
        beacon_interval: float = 3.0
    ):
        self.node_id = node_id or f"aos-node-{uuid.uuid4().hex[:6]}"
        self.broadcast_port = broadcast_port
        self.beacon_interval = beacon_interval
        self.peers: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def start(self):
        """Starts discovery listener and beacon broadcast threads."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()

        # Listener thread
        self.listener_thread = threading.Thread(target=self._listen_for_peers, daemon=True)
        self.listener_thread.start()

        # Beacon broadcaster thread
        self.broadcaster_thread = threading.Thread(target=self._broadcast_beacons, daemon=True)
        self.broadcaster_thread.start()

        print(f"[MeshSwarm] Sovereign P2P mesh node active: {self.node_id} (Port: {self.broadcast_port})")

    def stop(self):
        """Stops mesh networking."""
        self.is_running = False
        self._stop_event.set()
        print("[MeshSwarm] P2P mesh stopped.")

    def _listen_for_peers(self):
        """Listens for UDP broadcast packets from neighboring AOS edge devices."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('', self.broadcast_port))
            sock.settimeout(1.0)
        except Exception as e:
            print(f"[MeshSwarm] Could not bind UDP port: {e}")
            return

        while not self._stop_event.is_set():
            try:
                data, addr = sock.recvfrom(2048)
                message = json.loads(data.decode('utf-8'))
                sender_id = message.get("node_id")

                if sender_id and sender_id != self.node_id:
                    with self._lock:
                        self.peers[sender_id] = {
                            "node_id": sender_id,
                            "ip": addr[0],
                            "capabilities": message.get("capabilities", ["vector_search", "inference"]),
                            "last_seen": time.time(),
                            "status": "ONLINE"
                        }
            except socket.timeout:
                continue
            except Exception:
                continue
        sock.close()

    def _broadcast_beacons(self):
        """Broadcasts periodic presence heartbeat to local network subnet."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while not self._stop_event.is_set():
            beacon = {
                "node_id": self.node_id,
                "timestamp": time.time(),
                "capabilities": ["vector_search", "sandboxed_execution", "knowledge_graph"]
            }
            try:
                payload = json.dumps(beacon).encode('utf-8')
                sock.sendto(payload, ('<broadcast>', self.broadcast_port))
            except Exception:
                pass

            # Prune stale peers (> 15 seconds)
            with self._lock:
                now = time.time()
                for pid, info in list(self.peers.items()):
                    if now - info["last_seen"] > 15.0:
                        del self.peers[pid]

            time.sleep(self.beacon_interval)
        sock.close()

    def get_active_peers(self) -> List[Dict[str, Any]]:
        """Returns list of currently reachable edge nodes."""
        with self._lock:
            return list(self.peers.values())

    def delegate_task(self, peer_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates peer-to-peer compute task delegation."""
        with self._lock:
            peer = self.peers.get(peer_id)
        if not peer:
            return {"status": "ERROR", "message": f"Peer {peer_id} unreachable."}

        return {
            "status": "DELEGATED",
            "peer": peer_id,
            "task": task,
            "message": f"Task delegated to edge node {peer_id} at {peer['ip']}."
        }
