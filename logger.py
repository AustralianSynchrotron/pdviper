import logging
import sys
import os

title = 'PDViPeR'

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
