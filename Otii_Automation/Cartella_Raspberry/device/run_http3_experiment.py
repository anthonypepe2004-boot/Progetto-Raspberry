import os
import json
import logging
import subprocess
import time
import socket  # <--- USIAMO SOCKET INVECE DI SERIAL

from util import logger, network_status, upload_results, upload_logs

logger.setLevel(logging.INFO)

# Configurazione Sincronizzazione
SYNC_PORT = 5000  # Porta arbitraria per la sync

def run_http3_experiment(params):
    """
    Run HTTP/3 experiment con sincronizzazione via SOCKET (Wi-Fi/Lan)
    """
    implementations = [
        "quiche_version",
        "openSSL_version",
        "ngtcp2_version"
    ]

    results_base = os.path.expanduser("~/Cartella_Raspberry/results")
    os.makedirs(results_base, exist_ok=True)
    
    server_ip = params['server_ip'] # IP del Mac

    for impl in implementations:
        curl_path = os.path.expanduser(f"~/Desktop/Implementazioni/{impl}/curl/src/curl")
        payload_files = params['payload_files']
        
        logger.info(f"Implementation: {impl}")

        for payload_file in payload_files:
            url = f"https://{server_ip}:8888/{payload_file}"
            
            for attempt in range(30):
                trace_name = f"{impl}_{payload_file}_{attempt+1}"
                result_dir = os.path.join(results_base, trace_name)
                os.makedirs(result_dir, exist_ok=True)

                network_status(os.path.join(result_dir, 'network_status.json'))
                
                # --- SINCRONIZZAZIONE START (SOCKET) ---
                try:
                    # Crea un socket per ogni tentativo (o riusa, ma così è più robusto)
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        logger.info(f"[{trace_name}] Connecting to sync server {server_ip}:{SYNC_PORT}...")
                        s.connect((server_ip, SYNC_PORT))
                        
                        # 1. Chiedo di iniziare
                        msg = f"START:{trace_name}"
                        s.sendall(msg.encode())
                        
                        # 2. Aspetto conferma "GO" dal Mac
                        data = s.recv(1024).decode()
                        if data != "GO":
                            logger.error("Sync failed, received: " + data)
                            continue # Salta questo tentativo o gestisci errore
                            
                        logger.info(f"[{trace_name}] SYNC OK. Downloading...")

                        # --- ESECUZIONE DOWNLOAD ---
                        start = time.time_ns()
                        res = subprocess.run(
                            [
                                curl_path, 
                                '--http3', 
                                '-k',
                                # --- AGGIUNTA HEADER NO-CACHE ---
                                '-H', 'Cache-Control: no-cache, no-store, private, max-age=0, s-maxage=0',
                                # --------------------------------
                                '-o', '/dev/null', 
                                url
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        stop = time.time_ns()
                        # ---------------------------
                        stop = time.time_ns()
                        # ---------------------------

                        # 3. Dico che ho finito
                        s.sendall(b"STOP")
                        
                        # (Opzionale) Aspetto ACK di stop
                        s.recv(1024)

                except Exception as e:
                    logger.error(f"SOCKET ERROR: {e}")
                    # Se fallisce la sync, decidi se continuare o fermarti
                    # break 

                result = {
                    'implementation': impl,
                    'payload': payload_file,
                    'attempt': attempt+1,
                    'url': url,
                    'start_ns': start,
                    'stop_ns': stop,
                    'return_code': res.returncode
                }
                
                # Salvataggio e Upload
                with open(os.path.join(result_dir, 'http3_result.json'), 'w') as f:
                    json.dump(result, f, indent=2)

                upload_results(params['server'], result, trace_name)

            upload_logs(params['server'], params['log_file'])