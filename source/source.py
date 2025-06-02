import socket
import time
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed


def wait_for_server(host, port, retries=10, delay=2):
    for i in range(retries):
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"[Source] Conectado com sucesso a {host}:{port}")
                return True
        except Exception as e:
            print(f"[Source] Tentativa {i + 1}/{retries} falhou: {e}")
            time.sleep(delay)
    return False


class Source:
    def __init__(self, lb1_host='lb1', lb1_port=5001, n_requests=100, concurrency=10):
        self.lb1_host = lb1_host
        self.lb1_port = lb1_port
        self.n_requests = n_requests
        self.concurrency = concurrency
        self.rtt_times = []

    def send_request(self, req_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.lb1_host, self.lb1_port))
                t_start = time.time()

                texts = [
                    f"Exemplo de texto número {req_id}",
                    "Esta é uma frase para teste",
                    "O serviço deve gerar embeddings para esses textos"
                ]

                request_data = {
                    "id": f"REQ-{req_id}",
                    "timestamps": {
                        "T_saida": round(t_start, 6)
                    },
                    "texts": texts
                }

                s.sendall(json.dumps(request_data).encode())
                response_data = s.recv(8192)

                t_end = time.time()
                rtt = round(t_end - t_start, 6)

                response = json.loads(response_data.decode())
                timestamps = response.get("timestamps", {})
                
                print(f"[Source] Req {req_id} RTT: {rtt:.3f}s", flush=True)
                print(f"Resp: {response.get('id')}", flush=True)
                print(f"Timestamps: {timestamps}\n", flush=True)

                return rtt

        except Exception as e:
            print(f"[Source] Error in request {req_id}: {e}")
            return None


    def run(self):
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [executor.submit(self.send_request, i + 1) for i in range(self.n_requests)]
            for future in as_completed(futures):
                rtt = future.result()
                if rtt is not None:
                    self.rtt_times.append(rtt)

        total = len(self.rtt_times)
        avg_rtt = sum(self.rtt_times) / total if total > 0 else 0
        print(f"\n[Source] Total de requisições: {total}")
        print(f"[Source] Tempo médio de resposta (MRT): {avg_rtt:.3f} segundos")
        return avg_rtt

def gerar_grafico_comparativo(resultados, save_path="mrt_comparativo.png"):
    plt.figure(figsize=(10, 6))
    
    x_labels = [f"{r['n_requests']} reqs\n{r['concurrency']} conc." for r in resultados]
    mrt_values = [r["mrt"] for r in resultados]

    x = range(len(resultados))

    plt.plot(x, mrt_values, marker='o', linestyle='-', color='blue', label='MRT')

    plt.xticks(x, x_labels)
    plt.title("MRT por configuração de carga")
    plt.xlabel("Cenário de teste (Requisições / Concorrência)")
    plt.ylabel("MRT (segundos)")
    plt.grid(True)
    plt.tight_layout()
    plt.legend()
    plt.savefig(save_path)
    plt.close()
    print(f"[Source] Gráfico comparativo salvo em: {save_path}")


if __name__ == "__main__":
    if not wait_for_server("lb1", 5001):
        print("[Source] Não foi possível se conectar ao lb1. Encerrando.")
        exit(1)

    test_configs = [
        {"n_requests": 10, "concurrency": 5},
        {"n_requests": 30, "concurrency": 10},
        {"n_requests": 50, "concurrency": 20},
        {"n_requests": 100, "concurrency": 50},
        {"n_requests": 150, "concurrency": 100},
    ]

    resultados = []

    for config in test_configs:
        print(f"\n--- Executando teste com {config['n_requests']} requisições e {config['concurrency']} concorrência ---")
        source = Source(
            n_requests=config["n_requests"],
            concurrency=config["concurrency"]
        )
        mrt = source.run()
        resultados.append({
            "n_requests": config["n_requests"],
            "concurrency": config["concurrency"],
            "mrt": mrt
        })

    os.makedirs("/mnt", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = f"/mnt/mrt_comparativo_{timestamp}.png"
    gerar_grafico_comparativo(resultados, save_path=output_path)
