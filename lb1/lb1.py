import socket
import threading
import json
import time
from queue import Queue
from services import service1_1, service1_2

SERVICES = [service1_1.process_request, service1_2.process_request]

class LoadBalancer1:
    def __init__(self, host='0.0.0.0', port=5001, max_workers=2):
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
            
            print(f"[LB1] Requisição recebida de {addr}", flush=True)
            self.request_queue.put((conn, addr, data))  # Enfileira a requisição
        except Exception as e:
            print(f"[LB1] Erro ao receber requisição: {e}", flush=True)
            conn.close()

    def process_queue(self):
        while True:
            conn, addr, data = self.request_queue.get()
            self.semaphore.acquire()  # Espera até que haja "slot" livre
            threading.Thread(target=self.process_request, args=(conn, addr, data)).start()

    def process_request(self, conn, addr, data):
        try:
            t_lb1_received = time.time()
            request = json.loads(data)
            request["timestamps"]["lb1_received"] = t_lb1_received
            request["timestamps"]["lb1_sent"] = time.time()

            service = self.round_robin()
            proc_result = service(json.dumps(request))

            conn.sendall(proc_result.encode())
        except Exception as e:
            print(f"[LB1] Erro ao processar requisição: {e}", flush=True)
        finally:
            conn.close()
            self.semaphore.release()  # Libera o "slot"

    def start(self):
        # Inicia thread que processa a fila
        threading.Thread(target=self.process_queue, daemon=True).start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"[LB1] Escutando em {self.host}:{self.port}...")
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    lb1 = LoadBalancer1(max_workers=2)  # pode ajustar o número de workers
    lb1.start()
