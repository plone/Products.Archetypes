import logging

logger = logging.getLogger('Archetypes')


def log(message, summary='', level=logging.INFO):
    logger.log(level, '%s \n%s', summary, message)
