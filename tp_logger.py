import logging
import tp_config

CFG = tp_config.CFG


def get_logger():
    """
    Set a logger and return it after set up. The logger will log to a file and to the stdout.
    :return: logger: the logging object for logging to log file and console.
    """
    # create log
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    # create file handler and set level according to configuration. Writing mode is 'w' instead of 'a'
    # so there is no need to delete log file each run.
    fh = logging.FileHandler(CFG["Log"]["Log_File"], mode="w")
    ch = logging.StreamHandler()
    fh.setLevel(CFG["Log"]["File_Log_Level"])
    ch.setLevel(CFG["Log"]["Console_Log_Level"])
    # create formatter
    formatter = logging.Formatter(CFG["Log"]["Log_Format"])
    # add formatter to the handlers handler
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add handlers to log
    log.addHandler(ch)
    log.addHandler(fh)
    return log