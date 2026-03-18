import os
import logging
import datetime
from sys import stdout

from .mode import Mode


class Environment(object):
    # Logging configuration
    log_time_format = '%Y-%m-%d %H:%M:%S'
    log_format = '[%(asctime)s][%(name)-15s][%(levelname)-7s] - %(message)s'
    log_level = logging.DEBUG

    # Runtime metadata
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
    trace_counter = 1
    iteration = 0
    
    # AGGIUNTA FONDAMENTALE: Dizionario per la configurazione
    config = {} 

    # Experiment directories
    base_dir: str
    otii_dir: str
    log_dir: str
    log_file: str

    payload_dir = '/Users/antoniopepe/Desktop/Cartella_Mac/Caddy/payloads'

    @classmethod
    def init(cls, experiment: bool = True):
        """
        Initialize controller environment (Mac only).
        Sets up result directories, logging and experiment metadata.
        """

        if hasattr(cls, 'instance'):
            return Mode.CONTROLLER

        cls.instance = super(Environment, cls).__new__(cls)

        # Base results directory (relative to project root)
        cls.base_dir = os.path.join(
            'results',
            'http3_energy_experiment',
            cls.timestamp
        )

        cls.otii_dir = os.path.join(cls.base_dir, 'otii')
        cls.log_dir = os.path.join(cls.base_dir, 'logs')
        cls.log_file = os.path.join(cls.log_dir, 'controller.log')

        # Create directories
        os.makedirs(cls.base_dir, exist_ok=True)
        os.makedirs(cls.otii_dir, exist_ok=True)
        os.makedirs(cls.log_dir, exist_ok=True)

        # Logging setup
        logging.basicConfig(
            level=cls.log_level,
            format=cls.log_format,
            datefmt=cls.log_time_format,
            filename=cls.log_file
        )

        if experiment:
            stdout_handler = logging.StreamHandler(stdout)
            stdout_handler.setLevel(logging.INFO)
            stdout_handler.setFormatter(
                logging.Formatter(cls.log_format, cls.log_time_format)
            )
            logging.getLogger().addHandler(stdout_handler)

        logging.info('Controller environment initialized')
        logging.info(f'Results directory: {cls.base_dir}')
        logging.info(f'Payload directory: {cls.payload_dir}')

        return Mode.CONTROLLER

    def __str__(self):
        return f"Environment(base_dir={self.base_dir}, payload_dir={self.payload_dir})"