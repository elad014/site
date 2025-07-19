import logging
import os
import sys

class Utils:

    @staticmethod
    def read_version():
        with open('version.txt','r') as file:
            version = file.read()
        return version

    @staticmethod
    def read_log():
        log = ""
        with open("log.txt", 'r') as file:
            log = file.read()  # Read all lines into a list
        return log  # Serve main.html from templates/

    @staticmethod
    def clean_log():
        print("[INFO] Cleaning log file!!!")
        with open("log.txt", 'w') as file:
            file.write("")
            
class Logger(logging.Logger):
    @staticmethod
    def setup_logger(name):
        """Configure and return a logger with the specified name"""
        logger = logging.getLogger(name)
        
        if not logger.handlers:
            # Create a formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            # Create a console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            
            # Add the handler to the logger
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)
        
        return logger 