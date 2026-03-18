import logging
import traceback
from otii_automation.environment import Environment as Env
from otii_automation import Mode


from otii_automation.controller.controller import controller

def main():
    """
    Entry point: Inizializza l'ambiente e passa il controllo al controller Otii/Socket.
    """
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

        mode = Env.init()

        if mode != Mode.CONTROLLER:
            raise RuntimeError(
                f"run_controller.py avviato in modalità {mode}, atteso CONTROLLER"
            )

        logging.info("Starting OTII Automation controller (MAC)")
        
        # Avvia il loop del server (definito in controller.py)
        controller()

    except Exception as ex:
        logging.error("Main crashed")
        logging.error(ex)
        logging.error(traceback.format_exc())


if __name__ == "__main__":
    main()