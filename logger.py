import logging
import sys

# Processing log
LOG_FILENAME = 'logfile.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,
                    format='%(asctime)-24s %(message)s')
logger = logging.getLogger(LOG_FILENAME)


# Error log
ERRORLOG_FILENAME = 'error.log'
logging.basicConfig(filename=ERRORLOG_FILENAME, level=logging.DEBUG,
                    format='%(asctime)-24s %(message)s')
errorlogger = logging.getLogger(ERRORLOG_FILENAME)

def my_excepthook(excType, excValue, traceback, logger=errorlogger):
    '''
    A handler for logging tracebacks
    From http://stackoverflow.com/questions/1508467/how-to-log-my-traceback-error
    '''
    logger.error("An exception occurred",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = my_excepthook
