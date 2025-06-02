import socket
import time
import json
import hashlib

LB2_HOST = 'lb2'
LB2_PORT = 6001

def complex_hash_calc(text, iterations=100000):
    """
    Função altamente custosa para simular processamento intensivo.
    """
    result = text.encode('utf-8')
    MOD = 2**61 - 1  # número primo grande para exponenciação modular
    for i in range(iterations):
        h = hashlib.sha256(result + i.to_bytes(4, 'little')).digest()
        num = int.from_bytes(h, 'big')
        # Exponenciação modular custosa
        num = pow(num, 65537, MOD)
        # Mistura com constante e modular para limitar tamanho
        processed = (num * 2654435761) % MOD
        # Prepara resultado para próxima iteração
        result = processed.to_bytes(8, 'big')
    return int.from_bytes(result, 'big')

def process_request(data_str):
    try:
        request = json.loads(data_str)
        req_id = request.get("id", "UNKNOWN")
        timestamps = request.get("timestamps", {})
        lb1_received = timestamps.get("lb1_received")

        print(f"[Service1.1] Processando {req_id} ...", flush=True)

        t_service_received = time.time()
        timestamps["service_received"] = round(t_service_received, 6)

        if lb1_received is not None:
            timestamps["T_lb1_to_service1"] = round(t_service_received - lb1_received, 6)
        else:
            timestamps["T_lb1_to_service1"] = None

        texts = request.get("texts", [])
        if not texts:
            raise ValueError("Campo 'texts' não encontrado ou vazio na requisição")

        # Gera hashes extremamente custosos para cada texto
        hashes = [complex_hash_calc(text) for text in texts]

        request["hashes"] = hashes

        t_service_sent = time.time()
        timestamps["service_sent"] = round(t_service_sent, 6)

        request["timestamps"] = timestamps

        # Envia JSON atualizado para LB2
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LB2_HOST, LB2_PORT))
            s.sendall(json.dumps(request).encode())
            resp_data = s.recv(4096).decode()

        return resp_data

    except Exception as e:
        print(f"[Service1.1] Erro: {e}", flush=True)
        return json.dumps({
            "id": "ERROR",
            "timestamps": {},
            "error": str(e)
        })
