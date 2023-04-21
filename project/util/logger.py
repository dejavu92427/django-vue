
import logging
import json


def log(context, __name__):
    logger = logging.getLogger(__name__)
    logger.info(json.dumps(context, indent=4))
