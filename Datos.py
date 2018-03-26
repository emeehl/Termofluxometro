# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 22:43:52 2017

@author: slimbook
"""

import numpy as np
from configuracion import sensores

tipo = np.dtype([('data', 'object'), ('sensor', 'U44'), ('valores', 'object')])

class Datos:
    def __init__(self):
        self.temp = np.array([], tipo)
    
    def engadir(self, agora, topic, valores):
        condicion = (self.temp['data'] == agora) & \
                    (self.temp['sensor'] == topic)
        # Se xa existen valores para un tempo determinado...
        if(self.temp.size > 0 and self.temp[condicion]):
            # ...engádeos ao final
            self.temp[condicion]['valores'][0].extend(valores)
        else:
            # Se non crea unha nova entrada con eses valores para o sensor e tempo preciso
            self.temp = np.append(self.temp, np.array([(agora, topic, valores)], \
                                                        dtype=tipo))
            
    def calcularTransmitancia(self, datas, fluxo='horizontal'):
        # Coeficiente de conveccim2K
        conveccion = {'horizontal':  7.69,
                      'ascendente':  10.0,
                      'descendente': 5.88}
        hsi = conveccion[fluxo]
        if(type(datas) is list and len(datas) == 2):
            condicion = (self.temp['data'] >= datas[1]) & (self.temp['data'] <= datas[0])
            datos = self.temp[condicion]
        elif(datas is None):
            datos = self.temp
        else:
            condicion = (self.temp['data'] == datas)
            datos = self.temp[condicion]
        # Seleccionamos por sensor
        ti = datos[datos['sensor'] == sensores['AmbienteInterior']]['valores']
        tsi = datos[datos['sensor'] == sensores['ParedeInterior']]['valores']
        te = datos[datos['sensor'] == sensores['AmbienteExterior']]['valores']
        # Concatenamos todos os valores atopados, nun único np.array (array unidimensional)
        # e desbotamos os valores que non están dentro do rango de medida do DS18b20
        # incluíndo o código de erro -127.0
        try:
            ti = np.concatenate(ti, axis=0); ti[(ti<-55) | (ti>125)] = np.nan
            tsi = np.concatenate(tsi, axis=0); tsi[(tsi<-55) | (tsi>125)] = np.nan
            te = np.concatenate(te, axis=0); te[(te<-55) | (te>125)] = np.nan
            
            # Calculamos a media de cada sensor para o tempo dado
            ti = ti[~np.isnan(ti)].mean(); tsi = tsi[~np.isnan(tsi)].mean(); te = te[~np.isnan(te)].mean()
            
            U = hsi * (ti - tsi) / (ti - te)
            U = np.around(U, decimals=2)
        except ValueError:
            U = None
        return(U)

