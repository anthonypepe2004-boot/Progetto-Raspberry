import os
import json
import logging
import subprocess
import time

from util import logger, network_status, upload_results, upload_logs  # import locale

logger.setLevel(logging.INFO)

def device_main():
    """
    Funzione principale da chiamare sul Raspberry Pi
    """
    raspberry_config = {
        'server_ip': '192.168.116.120',  # IP Mac
        'payload_files': [
            'file_128b.bin',
            'file_1k.bin',
            'file_8k.bin',
            'file_64k.bin',
            'file_512k.bin',
            'file_4m.bin',
        ],
        'server': {
            'host': '192.168.116.120',  # IP Mac
            'username': 'antoniopepe',     # SSH user sul Mac
            'key_file': '/home/apepe11/.ssh/id_rsa',
            'remote_path': '/Users/antoniopepe/Desktop/Cartella_MAC/results'
        },
        'log_file': '/home/apepe11/Cartella_Raspberry/logs/device.log'
    }

    os.makedirs(os.path.dirname(raspberry_config['log_file']), exist_ok=True)
    os.makedirs(os.path.expanduser('~/Cartella_Raspberry/results'), exist_ok=True)

    from run_http3_experiment import run_http3_experiment
    run_http3_experiment(raspberry_config)

if __name__ == "__main__":
    device_main()