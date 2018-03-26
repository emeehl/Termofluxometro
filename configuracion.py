# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 01:04:52 2017

@author: slimbook
"""

# Canais (topics)
xeral = 'emeehl/transmitancia/'
sensores = {'AmbienteExterior':    xeral + 'SensorExterior/Ambiente', \
            'ParedeExterior':      xeral + 'SensorExterior/Parede', \
            'AmbienteInterior':    xeral + 'SensorInterior/Ambiente', \
            'ParedeInterior':       xeral + 'SensorInterior/Parede'}
resultados = {'minutal':      xeral + 'resultados/minutal',
              'dezminutal':   xeral + 'resultados/dezminutal',
              'instantaneo':   xeral + 'resultados/instantaneo', 
              'resume':        xeral + 'resultados/resume'}
xestion = {'ordes': xeral + 'ordes'} #Posibles ordes: empezar, pausar, enviar1min, enviar10min,
                         #                enviarThing, enviarResume
ordes = ['recibir', 'pausar', 'enviar', 'enviar1min', 'enviar10min', \
         'enviarResume', 'enviarInst']