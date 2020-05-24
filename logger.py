import logging

LOG_FILENAME = "log.txt"


logger = logging.getLogger("snahp_cron")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOG_FILENAME)
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)
