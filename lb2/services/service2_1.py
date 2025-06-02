import time
import json
import numpy as np

def process_request(data_str):
    try:
        request = json.loads(data_str)
        req_id = request.get("id", "UNKNOWN")
        timestamps = request.get("timestamps", {})

        print(f"[Service2.1] Processando {req_id} ...", flush=True)

        t_service_received = time.time()
        timestamps["service2_1_received"] = round(t_service_received, 6)

        lb2_sent = timestamps.get("lb2_sent")
        if lb2_sent is not None:
            timestamps["T_lb2_to_service2_1"] = round(t_service_received - lb2_sent, 6)
        else:
            timestamps["T_lb2_to_service2_1"] = None

        
        size = 1000  
        A = np.random.rand(size, size)
        B = np.random.rand(size, size)
        result_matrix = np.dot(A, B)

        # Apenas extrai a média para evitar enviar toda a matriz
        result_summary = {
            "mean_value": float(np.mean(result_matrix)),
            "max_value": float(np.max(result_matrix)),
            "min_value": float(np.min(result_matrix)),
        }

        t_service_sent = time.time()
        timestamps["service2_1_sent"] = round(t_service_sent, 6)

        request["timestamps"] = timestamps
        request["matrix_stats"] = result_summary

        return json.dumps(request)

    except Exception as e:
        print(f"[Service2.1] Erro: {e}", flush=True)
        return json.dumps({
            "id": "ERROR",
            "timestamps": {},
            "error": str(e)
        })
