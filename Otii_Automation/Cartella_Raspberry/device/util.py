import json
import logging
import os
import subprocess
import ifcfg
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient


#installa le dipendenze sul raspberry
# c'è il file 


logger = logging.getLogger('device')
logger.setLevel(logging.INFO)

# Comando per abilitare interfaccia di rete
iface_up_cmd = 'sudo ifconfig eth0 up'


def network_status(output_path: str):
    """Salva informazioni sulle interfacce di rete in JSON"""
    interfaces = {iface['device']: iface for iface in ifcfg.interfaces().values()}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as fout:
        json.dump(interfaces, fout, indent=2)
    return interfaces


def upload_results(server: dict, local_results: dict, trace: str):
    """Upload dei risultati JSON al Mac via SCP"""
    tmp_file = '.tmp_results.json'
    with open(tmp_file, 'w') as f:
        json.dump(local_results, f)

    try:
        with SSHClient() as ssh:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(hostname=server['host'],
                        username=server['username'],
                        key_filename=server['key_file'])
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(tmp_file, os.path.join(server['remote_path'], f'{trace}.json'))
        os.remove(tmp_file)
        logger.info(f"Results uploaded: {trace}")
    except Exception as ex:
        logger.warning(f"Upload results failed: {ex}")


def upload_logs(server: dict, log_file: str):
    """Upload log file al Mac via SCP"""
    try:
        with SSHClient() as ssh:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(hostname=server['host'],
                        username=server['username'],
                        key_filename=server['key_file'])
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(log_file, os.path.join(server['remote_path'], 'device.log'))
        logger.info("Logs uploaded")
    except Exception as ex:
        logger.warning(f"Upload logs failed: {ex}")