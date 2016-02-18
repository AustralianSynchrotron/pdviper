import logging
import sys
import os

#from app import title
title = 'PDViPeR'

'''
class SingleLevelFilter(logging.Filter):
    """
    From http://stackoverflow.com/questions/1383254/logging-streamhandler-and-standard-streams
    """
    def __init__(self, passlevel, reject):
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record):
        if self.reject:
            return (record.levelno != self.passlevel)
        else:
            return (record.levelno == self.passlevel)


It turns out that Traits exceptions are handled differently to normal Python exceptions,
so my attempts to direct them to an errorlog file won't work unless a custom exception
handler is pushed onto the handler stack. See
https://svn.enthought.com/enthought/wiki/NotificationExceptionHandlers

However, it appears that the traceback object is not made available so I can't log it in
a useful way.

def my_traits_exception_handler( object, trait_name, old_value, new_value ):
    try:
        errorlogger.error("An exception {object} occurred in trait {trait_name}".format(\
                 object=repr(object),trait_name=trait_name))
        errorlogger.error(traceback.extract_tb(object))
    except IOError:
        pass

push_exception_handler(handler=my_traits_exception_handler, reraise_exceptions=True)
'''


# Set path to logfiles to environment variable HOME if it exists, else to HOMEPATH if it
# exists, else to the current working directory.
logfiles_path = os.getenv('HOME') or os.getenv('HOMEPATH') or os.getcwd()

# Logfile names and paths
LOG_DIRECTORY = os.path.join(logfiles_path, '.{}'.format(title))
LOG_FILENAME = os.path.join(logfiles_path, '.{}'.format(title), 'logfile.log')
ERRORLOG_FILENAME = os.path.join(logfiles_path, '.{}'.format(title), 'error.log')

# Try creating directory if it doesn't exist
try:
    os.mkdir(LOG_DIRECTORY)
    print 'Created logfile directory', LOG_DIRECTORY
except OSError:
    # Something exists already, or it can't be written
    pass

try:
    with open(LOG_FILENAME, 'a+') as f:
        pass
    event_logger_writeable = True
except IOError:
    print '{} unwriteable. Event logging disabled.'.format(LOG_FILENAME)
    event_logger_writeable = False

#logging.basicConfig(filename=LOG_FILENAME, format='%(asctime)-24s %(message)s')
logger = logging.getLogger(LOG_FILENAME)
handler = logging.FileHandler(LOG_FILENAME)
formatter = logging.Formatter('%(asctime)-24s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate=False
# If we can't create a logfile, as determined above, set the logger level to not log
# INFO (or for the errorlogger DEBUG) messages; basically only attempt to log if the
# program is going to crash anyway. This should effectively disable logging.
if event_logger_writeable:
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.CRITICAL)
## logger.addFilter(SingleLevelFilter(logging.INFO, False))


# Error log
try:
    with open(ERRORLOG_FILENAME, 'a+') as f:
        pass
    error_logger_writeable = True
except IOError:
    print '{} unwriteable. Error logging disabled.'.format(ERRORLOG_FILENAME)
    error_logger_writeable = False

#logging.basicConfig(filename=ERRORLOG_FILENAME, format='%(asctime)-24s %(message)s')
errorlogger = logging.getLogger(ERRORLOG_FILENAME)
error_handler = logging.FileHandler(LOG_FILENAME)
error_formatter = logging.Formatter('%(asctime)-24s %(message)s')
error_handler.setFormatter(error_formatter)
errorlogger.addHandler(error_handler)
errorlogger.propagate=False
if error_logger_writeable:
    errorlogger.setLevel(logging.DEBUG)
else:
    errorlogger.setLevel(logging.CRITICAL)
## errorlogger.addFilter(SingleLevelFilter(logging.INFO, True))
## h2 = logging.StreamHandler(sys.stderr)
## f2 = SingleLevelFilter(logging.INFO, True)
## h2.addFilter(f2)


def my_excepthook(excType, excValue, traceback, errorlogger=errorlogger):
    """
    A handler for logging tracebacks
    From http://stackoverflow.com/questions/1508467/how-to-log-my-traceback-error
    """
    try:
        errorlogger.error("An exception occurred",
                 exc_info=(excType, excValue, traceback))
    except IOError:
        pass

sys.excepthook = my_excepthook
