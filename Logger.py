import logging

def get_logger():
    logger = logging.getLogger(__name__)
    handler = logging.FileHandler('offers2.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.debug("Prueba log")
    return logger

_logger = get_logger()


