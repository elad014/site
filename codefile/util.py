import os
import sys


class Util:

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