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

#t.sleep(20)

import logging
import logging.handlers
import sys

LOG_FILENAME = "/tmp/transmitancia.log"
LOG_LEVEL = logging.INFO

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, \
            when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s 5(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class MyLogger(object):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        
    def write(self, message):
        if message.rstrip() != "":
            self.logger.log(self.level, message.restrip())
            
sys.stdout = MyLogger(logger, logging.INFO)
sys.stderr = MyLogger(logger, logging.ERROR)


## Canais (topics)
#xeral = 'emeehl/transmitancia/'
#sensores = {'AmbienteExterior':    xeral + 'SensorExterior/Ambiente', \
#            'ParedeExterior':      xeral + 'SensorExterior/Parede', \
#            'AmbienteInterior':    xeral + 'SensorInterior/Ambiente', \
#            'ParedeInterior':       xeral + 'SensorInterior/Parede'}
#resultados = {'minutal':      xeral + 'resultados/minutal',
#              'dezminutal':   xeral + 'resultados/dezminutal',
#              'instantaneo':   xeral + 'resultados/instantaneo', 
#              'resume':        xeral + 'resultados/resume'}
#xestion = {'ordes': xeral + 'ordes'} #Posibles ordes: empezar, pausar, enviar1min, enviar10min,
#                         #                enviarThing, enviarResume
#ordes = ['recibir', 'pausar', 'enviar', 'enviar1min', 'enviar10min', \
#         'enviarResume', 'enviarInst']

#tipo = np.dtype([('data', 'object'), ('sensor', 'U44'), ('valores', 'object')])
#temps = np.array([], tipo)
temps = Datos()

minutal = dt.datetime.utcnow().minute

# Estados do autómata: disposto a recibir e enviando
recibirOk = False
enviando = False

def on_connect(client, userdata, flags, rc):
    global minutal
    print("Conectado co rc: " + str(rc))
    # Cada vez que conecta co servidor mqtt
    client.subscribe(xeral + "#")            # Suscribimos a todas as canles
    client.publish(xestion['ordes'], 'pausar')        # Estado a Off. Agardamos sinal de On
    minutal = dt.datetime.utcnow().minute    # Actualizamos tempo de referencia


def on_message(client, userdata, msg):
    global temps, minutal, recibirOk, enviando
    now = dt.datetime.utcnow()
    agora = now.strftime("%Y%m%d_%H%M")
    topic = str(msg.topic); mensaxe = msg.payload.decode('utf-8')
    if(topic in xestion.values() and mensaxe in ordes):
        sys.stdout.write('Mensaxe recibida')
        if('pausar' in mensaxe):
            recibirOk = False
        elif('recibir' in mensaxe):
            minutal = dt.datetime.utcnow().minute    # Actualizamos tempo de referencia
            recibirOk = True
            print('Recibindo ok')
            logger.info('Recibindo ok')
        elif('enviar' in mensaxe):
            enviar(mensaxe)
    elif(recibirOk and topic in sensores.values()):
        valores_raw = re.findall(r'-{0,1}\d+.\d+', mensaxe)
        valores = [float(i) for i in valores_raw]
        temps.engadir(agora, topic, valores)
##        valores = [float(i) for i in mensaxe[:-2].split('; ')]
#        # Se xa existen valores para un tempo determinado...
#        if(temps.size > 0 and temps[(temps['data'] == agora) & (temps['sensor'] == topic)]):
#            condicion = (temps['data'] == agora) & (temps['sensor'] == topic)
#            # ...engádeos ao final
#            temps[condicion]['valores'][0].extend(valores)
#        else:
#            # Se non crea unha nova entrada con eses valores para o sensor e tempo preciso
#            temps = np.append(temps, np.array([(agora, topic, valores)], dtype=tipo))
        # Envíanse periodicamente resultados peticións de resultados minutais e 
        # dezminutais. Solicítase o envío cun minuto de retraso para dar tempo 
        # aos sensores enviaren as medidas e así acumular os resultados do minuto
        # anterior.
        # Como cada vez que se envía unha solicitude de minutal, actulízase o
        # tempo ao minuto seguinte, avalíase antes se o minuto é de fin de 
        # dezminutal, para solicitar o mesmo.
        print('enviando: ', enviando, ' minutal: ', minutal, ' now.minute-2: ', \
              (now.minute-2)%60, ' ok? ', not enviando and minutal == (now.minute-2)%60)
        mssg_log = 'enviando: ' + enviando, ' minutal: ' + minutal, ' now.minute-2: '+ \
                    (now.minute-2)%60 + ' ok? ' + \
                    (not enviando and minutal == (now.minute-2)%60)
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
#    condicion = (temps['data'] == data)
#    transmitancia = calcularTransmitancia(temps[condicion])
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
        print(response.status, response.reason)
        data = response.read()
        print(data)
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



#def calcularTransmitancia(datos):
#    hsi = 7.69       #W/m2K para cerramentos verticais
#    # Seleccionamos por sensor
#    ti = datos[datos['sensor'] == sensores['AmbienteInterior']]['valores']
#    tsi = datos[datos['sensor'] == sensores['ParedeInterior']]['valores']
#    te = datos[datos['sensor'] == sensores['AmbienteExterior']]['valores']
#    # Concatenamos todos os valores atopados, nun único np.array (array unidimensional)
#    # e desbotamos os valores que non están dentro do rango de medida do DS18b20
#    # incluíndo o código de erro -127.0
##    print(datos)
##    print(ti); print(tsi); print(te)
#    try:
#        ti = np.concatenate(ti, axis=0); ti[(ti<-55) | (ti>125)] = np.nan
#        tsi = np.concatenate(tsi, axis=0); tsi[(tsi<-55) | (tsi>125)] = np.nan
#        te = np.concatenate(te, axis=0); te[(te<-55) | (te>125)] = np.nan
#        
#        # Calculamos a media de cada sensor para o tempo dado
#        ti = ti[~np.isnan(ti)].mean(); tsi = tsi[~np.isnan(tsi)].mean(); te = te[~np.isnan(te)].mean()
#        
#        U = hsi * (ti - tsi) / (ti - te)
#        U = np.around(U, decimals=2)
#    except ValueError:
#        U = None
#    return(U)



if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("192.168.3.1", 1883, 60)
#    client.connect("iot.eclipse.org", 1883, 60)
    
    client.loop_start()  #Mellor loop_start, proporciona un fio non bloqueante
 #   client.loop_forever() #loop_forever proporciona un fío bloqueante

