import logging
import os
import time
import traceback

from otii_tcp_client.otii import Otii
from otii_tcp_client.otii_connection import OtiiConnection
from otii_tcp_client.arc import Arc
from otii_tcp_client.recording import Recording
from otii_tcp_client.project import Project

from ...environment import Environment as Env

logger = logging.getLogger('otii')

class SimpleOtii:
    def __init__(self):
        # Connessione al server Otii
        connection = OtiiConnection(Env.config['otii']['hostname'], Env.config['otii']['port'])
        connection.connect_to_server(try_for_seconds=3)

        self.otii = Otii(connection)
        
        try:
            self.otii.login(Env.config['otii']['license_user'], Env.config['otii']['license_psw'])
        except Exception as e:
            logger.warning(f"Login saltato: {e}")

        self.project: Project = None
        self.arc: Arc = None
        
        # Variabili per calcolare la durata manualmente
        self._start_ts = 0.0
        self._stop_ts = 0.0

    def create_project(self) -> None:
        if self.project is not None:
            try: self.project.close()
            except: pass

        self.project = self.otii.create_project()
        self._init_device()

    def start_recording(self) -> None:
        if self.project:
            self.project.start_recording()
            # FIX: Segniamo il tempo di inizio manuale
            self._start_ts = time.time()

    def stop_recording(self, trace_name: str) -> None:
        self.project.stop_recording()
        # FIX: Segniamo il tempo di fine manuale
        self._stop_ts = time.time()
        
        time.sleep(0.2)
        
        recordings = self.project.get_recordings()
        if recordings:
            recordings[-1].rename(trace_name)

    def save_project(self, path: str) -> None:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        full_path = os.path.abspath(path)
        self.project.save_as(full_path, force=True)

    def get_last_statistics(self) -> dict:
        """ 
        Restituisce energia (J) e durata (s).
        Usa il tempo calcolato da Python per evitare errori della libreria Otii.
        """
        recording: Recording = self.project.get_last_recording()
        
        # 1. Calcolo durata basato sui timestamp Python (più sicuro)
        duration = self._stop_ts - self._start_ts
        if duration <= 0: duration = 0.1 # Evita errori di divisione
        
        # 2. Chiediamo a Otii SOLO la media della corrente (average)
        # Passiamo 0 come inizio e la durata calcolata
        stats = recording.get_channel_statistics(self.arc.id, 'mc', 0, duration)
        
        avg_current = stats['average'] # Ampere
        voltage = 5.0 
        
        # Energia = Potenza Media * Tempo
        energy_j = (avg_current * voltage) * duration
        
        return {
            "energy_j": energy_j,
            "duration_s": duration
        }

    def _init_device(self):
        devices = self.otii.get_devices()
        if not devices: raise Exception("Nessun Arc collegato!")
        self.arc = devices[0]
        
        self.arc.set_range("high")
        self.arc.set_main_voltage(5)
        self.arc.set_max_current(4.5)
        self.arc.enable_channel('mc', True)
        self.otii.set_all_main(True)
        time.sleep(1.0)