#!/usr/bin/python3.4
# -*- coding: utf-8 -*-


import logging, datetime, time

LOG_FILENAME = '/tmp/transmitancia.log'
LOG_LEVEL = logging.INFO

#Crear o logger e conectarse a el
logger = logging.getLoger('Termoflux')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s: %(name)s - %(message)s', \
                datefmt = '%Y%m%d %H:%M:%S')

#Crear manipulador do logging, formato, etc
fh = logging.StreamHandler(LOG_FILENAME)
fh.setLevel(LOG_LEVEL)
fh.setFormatter(formatter)

#Conectar o manipulador co logger
logger.addHandler(fh)



