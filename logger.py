import logging
import sys

#LOG_FILENAME = os.path.join(os.path.split(sys.argv[0])[0], 'logfile.log')
LOG_FILENAME = 'logfile.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG,
                    format='%(asctime)-24s %(message)s')
logger = logging.getLogger(LOG_FILENAME)

def my_excepthook(excType, excValue, traceback, logger=logger):
    '''
    A handler for logging tracebacks
    From http://stackoverflow.com/questions/1508467/how-to-log-my-traceback-error
    '''
    logger.error("An exception occurred",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = my_excepthook  
