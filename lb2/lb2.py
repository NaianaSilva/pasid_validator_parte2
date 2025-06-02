import socket
import threading
import time
import json
from queue import Queue
from services import service2_1, service2_2

SERVICES = [service2_1.process_request, service2_2.process_request]

class LoadBalancer2:
    def __init__(self, host='0.0.0.0', port=6001, max_workers=2):
        self.host = host
        self.port = port
        self.current = 0
        self.request_queue = Queue()
        self.semaphore = threading.Semaphore(max_workers)

    def round_robin(self):
        svc = SERVICES[self.current]
        self.current = (self.current + 1) % len(SERVICES)
        return svc

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(2048).decode()
            print(f"[LB2] Requisição recebida de {addr}", flush=True)
            self.request_queue.put((conn, addr, data))  # Enfileira a requisição
        except Exception as e:
            print(f"[LB2] Erro ao receber requisição: {e}", flush=True)
            conn.close()

    def process_queue(self):
        while True:
            conn, addr, data = self.request_queue.get()
            self.semaphore.acquire()
            threading.Thread(target=self.process_request, args=(conn, addr, data)).start()

    def process_request(self, conn, addr, data):
        try:
            t_lb2_received = time.time()

            request = json.loads(data)
            if "timestamps" not in request:
                request["timestamps"] = {}

            timestamps = request["timestamps"]
            timestamps["lb2_received"] = round(t_lb2_received, 6)

            # Calcula tempo service1 -> lb2
            service_sent = timestamps.get("service_sent")
            timestamps["T_service1_to_lb2"] = round(t_lb2_received - service_sent, 6) if service_sent else None

            # Timestamp de saída do LB2
            timestamps["lb2_sent"] = round(time.time(), 6)

            # Chama o service via round-robin
            updated_data = json.dumps(request)
            service = self.round_robin()
            result = service(updated_data)

            conn.sendall(result.encode())

        except Exception as e:
            print(f"[LB2] Erro ao processar requisição: {e}", flush=True)
        finally:
            conn.close()
            self.semaphore.release()

    def start(self):
        threading.Thread(target=self.process_queue, daemon=True).start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"[LB2] Escutando em {self.host}:{self.port}...")
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    lb2 = LoadBalancer2(max_workers=2)  # ajustável conforme capacidade dos serviços
    lb2.start()
