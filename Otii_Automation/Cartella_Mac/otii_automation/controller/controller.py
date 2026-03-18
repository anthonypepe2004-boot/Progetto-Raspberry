import socket
import logging
import traceback
import os
import time
import json

from ..environment import Environment as Env
from .otii import SimpleOtii

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('controller')

SYNC_HOST = '0.0.0.0'
SYNC_PORT = 5005
SAVE_PATH = os.path.expanduser("~/Desktop/Cartella_Mac/otii_data")
RESULTS_JSON_PATH = os.path.expanduser("~/Desktop/Cartella_Mac/results_json")

def controller() -> None:
    Env.config = {
        'otii': {
            'hostname': '127.0.0.1', 'port': 4444,
            'license_user': 'antonio1234', 'license_psw': 'Antonio0000!'
        }
    }

    os.makedirs(SAVE_PATH, exist_ok=True)
    os.makedirs(RESULTS_JSON_PATH, exist_ok=True)

    try:
        logger.info("Avvio Controller...")
        otii = SimpleOtii()
        try: otii.create_project()
        except: pass

        all_energy_data = {}
        all_time_data = {}
        current_trace_name = "init"
        current_base_name = "unknown"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((SYNC_HOST, SYNC_PORT))
            server_sock.listen(5)
            logger.info(f"--- CONTROLLER PRONTO SU PORTA {SYNC_PORT} ---")

            while True:
                # Accetta una nuova connessione dal Raspberry
                conn, addr = server_sock.accept()
                conn.settimeout(10.0)
                
                try:
                    with conn:
                        # --- MODIFICA CRITICA: LOOP INTERNO ---
                        # Continua ad ascoltare sulla stessa connessione finché il Raspberry non chiude
                        while True:
                            data = conn.recv(1024)
                            if not data: 
                                break # Il Raspberry ha chiuso la connessione o finito il test
                            
                            msg_full = data.decode().strip()
                            
                            # Gestisce il caso (raro ma possibile) che START e STOP arrivino incollati
                            # Esempio msg_full: "START:xxxSTOP"
                            messages = []
                            if "START" in msg_full and "STOP" in msg_full:
                                parts = msg_full.split("STOP")
                                messages.append(parts[0]) # La parte START
                                messages.append("STOP")
                            else:
                                messages.append(msg_full)

                            for msg in messages:
                                if not msg: continue

                                # --- START ---
                                if msg.startswith("START"):
                                    try:
                                        full_name = msg.split(":")[1]
                                        current_trace_name = full_name
                                        current_base_name = full_name.split("_run")[0]
                                    except: current_base_name = "unknown"
                                    
                                    logger.info(f"--> START: {current_trace_name}")
                                    otii.start_recording()
                                    conn.sendall(b"GO")

                                # --- STOP ---
                                elif msg == "STOP":
                                    otii.stop_recording(current_trace_name)
                                    
                                    # Estrazione e Salvataggio
                                    try:
                                        stats = otii.get_last_statistics()
                                        e_val = stats['energy_j']
                                        t_val = stats['duration_s']
                                        
                                        logger.info(f"   DATI: {e_val:.4f} J | {t_val:.3f} s")

                                        if current_base_name not in all_energy_data:
                                            all_energy_data[current_base_name] = []
                                            all_time_data[current_base_name] = []
                                        
                                        all_energy_data[current_base_name].append(e_val)
                                        all_time_data[current_base_name].append(t_val)

                                        # SALVATAGGIO DISCO
                                        save_json_files(current_base_name, 
                                                      all_energy_data[current_base_name], 
                                                      all_time_data[current_base_name])

                                    except Exception as e:
                                        logger.error(f"Errore dati Otii: {e}")
                                    
                                    otii.save_project("current_backup.otii")
                                    conn.sendall(b"ACK")

                                # --- NEW_PROJECT ---
                                elif msg.startswith("NEW_PROJECT"):
                                    logger.info("--> NEW PROJECT")
                                    all_energy_data = {}
                                    all_time_data = {}
                                    otii.create_project()
                                    conn.sendall(b"READY")
                                
                                # --- QUIT ---
                                elif msg == "QUIT":
                                    logger.info("--> QUIT")
                                    try: otii.stop_recording("force_stop")
                                    except: pass
                                    conn.sendall(b"BYE")
                                    return # Esce dal controller

                except Exception as e:
                    logger.error(f"Errore connessione: {e}")

    except Exception as ex:
        logger.error(f"CRASH: {traceback.format_exc()}")

def save_json_files(base_name, energy_data, time_data):
    try:
        f_en = os.path.join(RESULTS_JSON_PATH, f"energy_{base_name}.json")
        with open(f_en, 'w') as f: json.dump(energy_data, f, indent=2)
            
        f_tm = os.path.join(RESULTS_JSON_PATH, f"time_{base_name}.json")
        with open(f_tm, 'w') as f: json.dump(time_data, f, indent=2)
            
        print(f"   [DISK WRITE] Aggiornato {base_name}: {len(energy_data)} campioni")
    except Exception as e:
        logger.error(f"Errore scrittura JSON: {e}")