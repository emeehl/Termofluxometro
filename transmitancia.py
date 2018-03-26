#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 12:19:22 2017

@author: slimbook
"""

import paho.mqtt.client as mqtt
from Datos import Datos
from configuracion import xeral, sensores, resultados, xestion, ordes
import re
import datetime as dt
import http.client, urllib
import time as t


import logging, datetime, time

LOG_FILENAME = '/tmp/transmitancia.log'
LOG_LEVEL = logging.DEBUG

#Crear o logger e conectarse a el
logger = logging.getLogger('Termoflux')
logger.setLevel(LOG_LEVEL)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s', \
                datefmt = '%Y%m%d %H:%M:%S')

#Crear manipulador do logging, formato, etc
fh = logging.FileHandler(LOG_FILENAME)
fh.setLevel(LOG_LEVEL)
fh.setFormatter(formatter)

#Conectar o manipulador co logger
logger.addHandler(fh)

temps = Datos()

minutal = dt.datetime.utcnow().minute

# Estados do autómata: disposto a recibir e enviando
recibirOk = False
enviando = False

def on_connect(client, userdata, flags, rc):
    logger.debug('Empezando on_connect()')
    global minutal
    logger.debug("Conectado co rc: " + str(rc))
    # Cada vez que conecta co servidor mqtt
    client.subscribe(xeral + "#")            # Suscribimos a todas as canles
    client.publish(xestion['ordes'], 'pausar')        # Estado a Off. Agardamos sinal de On
    minutal = dt.datetime.utcnow().minute    # Actualizamos tempo de referencia
    logger.debug('Rematando on_connect()')


def on_message(client, userdata, msg):
    global temps, minutal, recibirOk, enviando
    now = dt.datetime.utcnow()
    agora = now.strftime("%Y%m%d_%H%M")
    topic = str(msg.topic); mensaxe = msg.payload.decode('utf-8')
    if(topic in xestion.values() and mensaxe in ordes):
        logger.info('Mensaxe recibida')
        if('pausar' in mensaxe):
            recibirOk = False
        elif('recibir' in mensaxe):
            minutal = dt.datetime.utcnow().minute    # Actualizamos tempo de referencia
            recibirOk = True
            logger.info('Recibindo ok')
        elif('enviar' in mensaxe):
            enviar(mensaxe)
    elif(recibirOk and topic in sensores.values()):
        valores_raw = re.findall(r'-{0,1}\d+.\d+', mensaxe)
        valores = [float(i) for i in valores_raw]
        temps.engadir(agora, topic, valores)
        mssg_log = 'enviando: ' + str(enviando) + ' minutal: ' + str(minutal) + \
                   ' now.minute-2: '+ str((now.minute-2)%60) + ' ok? ' + \
                    str(not enviando and minutal == (now.minute-2)%60)
        logger.info(mssg_log)
        if(not enviando and minutal == (now.minute-2) % 60): #Envía minutal cun minuto de retraso
            enviando = True
            if(minutal % 10 == 0):  #Enviar 10minutal cun minuto de retraso
                client.publish(xestion['ordes'], 'enviar10min') 
            client.publish(xestion['ordes'], 'enviar1min')
#        print(temps) 


def enviar(entrada):
    switch = {'enviar1min':     enviar1min,
              'enviar10min':    enviar10min,
    #          'enviarThing':    enviarThing,
              'enviarInst':     enviarInst,
              'enviarResume':   enviarResume}
    func = switch.get(entrada, lambda: None)
    return func()


def enviarInst():
    global temps, minutal
    data = dt.datetime.utcnow().strftime("%Y%m%d_%H") + '{:02}'.format(minutal)
    transmitancia = temps.calcularTransmitancia(data, fluxo='horizontal')
    if(not transmitancia is None):
        client.publish(resultados['instantaneo'], transmitancia)
    else:
        pass



def enviar1min():
    '''
    Envía ao canal de resultados o valor da transmitancia calculado a partir
    dos valores de temperatura recollidos no úlitmo minuto.
    Mentres se está calculando e enviando o resultado, queda bloqueada a recepcción
    doutros mensaxes 'enviar1min', ao finalizar o envío actualízase o valor do
    minuto actual e desbloquéase a recepción de 'enviar1min'.
    O bloqueo da mensaxe 'enviar1min' faise capturando as mensaxes que aparezan
    e non facendo nada até que a variable global 'enviando' estea a True.
    '''
    global temps, minutal, enviando
    data = dt.datetime.utcnow().strftime("%Y%m%d_%H") + '{:02}'.format(minutal)
    transmitancia = temps.calcularTransmitancia(data, fluxo='horizontal')
#    condicion = (temps['data'] == data)
#    transmitancia = calcularTransmitancia(temps[condicion])
    if(not transmitancia is None):
        client.publish(resultados['minutal'], transmitancia)
        enviarThing(transmitancia)
    else:
        pass
    minutal = (minutal + 1) % 60
    enviando = False


def enviar10min():
    '''
    Envía ao canal de resultados o valor da transmitancia calculado a partir dos 
    valores de temperatura recollidos nos últimos 10 minnutos.
    Faise o envío despois de que se comprobe se o últimio minutal que se vai calcular
    corresponde cun dezminutal.
    '''
    global temps, minutal
    data = dt.datetime.utcnow().strftime('%Y%m%d_%H')
    datas = [data + '{:02}'.format(m) for m in list(range(minutal, minutal-10, -9))]
    transmitancia = temps.calcularTransmitancia(datas, fluxo='horizontal')
#    condicion = (temps['data'] >= datas[1]) & (temps['data'] <= datas[0])
#    transmitancia = calcularTransmitancia(temps[condicion])
    if(not transmitancia is None):
        client.publish(resultados['dezminutal'], transmitancia)
    else:
        pass



def enviarThing(valor):
    '''
    Envía valores dezminutais á web thingspeak.com
    En principio envíanse valores de transmitancia, pero pódense enviar
    os valores de temperatura tamén.
    '''
    params = urllib.parse.urlencode({'field1': valor, 'key': '6NZS0EBQ7X3MZX6L'})
    headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
    conn = http.client.HTTPConnection("api.thingspeak.com:80") 
    try:
        conn.request("POST", "/update", params, headers)
        response = conn.getresponse()
        logger.info('Resposta thingspeak.com: ' + response.status + response.reason)
        data = response.read()
        logger.info(data)
        conn.close()
    except:
        pass
    pass



def enviarResume():
    '''
    Envía o valor actual da transmitancia tendo en conta todos os valores recollidos
    até o momento.
    '''
    global temps
    datas = None
    transmitancia = temps.calcularTransmitancia(datas, fluxo='horizontal')
#    transmitancia = calcularTransmitancia(temps)
    if(not transmitancia is None):
        client.publish(resultados['resume'], transmitancia)
    else:
        pass


if __name__ == "__main__":
    logger.debug('Empeza o script')
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("192.168.3.1", 1883, 60)
#    client.connect("iot.eclipse.org", 1883, 60)
    
#    client.loop_start()  #Mellor loop_start, proporciona un fio non bloqueante
    client.loop_forever() #loop_forever proporciona un fío bloqueante
    logger.debug('Remata o script')

