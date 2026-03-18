import os
import json
import logging
from ..environment import Environment as Env

logger = logging.getLogger('controller')

def download_results(trace: str) -> dict:
    """
    Legge i risultati dell'esperimento dai file locali.
    """
    path = os.path.join('results', Env.timestamp, f'{trace}.json')
    if os.path.exists(path):
        try:
            with open(path, 'r') as fp:
                return json.load(fp)
        except Exception as ex:
            logger.warning(f"Errore nella lettura dei risultati {trace}: {ex}")
            return {}
    else:
        logger.warning(f"File dei risultati non trovato: {path}")
        return {}


def download_device_logs() -> None:
    """
    Copia i log del device nella cartella logs locale.
    """
    src = os.path.join('logs', 'device.log')
    dst = os.path.join(Env.log_dir, 'device.log')
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            with open(src, 'r') as f_src, open(dst, 'w') as f_dst:
                f_dst.write(f_src.read())
            logger.info(f"Log copiato in {dst}")
        except Exception as ex:
            logger.warning(f"Errore nella copia dei log: {ex}")
    else:
        logger.warning(f"File log non trovato: {src}")

def build_trace_name(params: dict) -> str:
    """
    Costruisce il nome del trace in base ai parametri.
    """
    trace_name = f'{Env.trace_counter}_{params["delay"]}_{params["bandwidth"].split("%")[0]}_{Env.iteration:03d}'
    return trace_name