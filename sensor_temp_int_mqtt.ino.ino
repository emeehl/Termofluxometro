#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ThingSpeak.h>
#include <PubSubClient.h>

// Pins datos:
//---------------------------------------------------------------
// GPIO14: D5
// GPIO12: D6
#define ONE_WIRE_BUS_PAREDE 14
#define ONE_WIRE_BUS_AMBIENTE 12

// WiFi RasPi
#define MAX_INTENTOS 50
#define WIFI_SSID "RaspiWiFi"
#define WIFI_PASS "p4ssw0rd"

WiFiClient wifiClient;

// MQTT
//---------------------------------------------------------------
const char* mqttServer = "192.168.3.1";
//const char* mqttServer = "iot.eclipse.org";
PubSubClient mqttClient(wifiClient);
// Comentar/descomentar segundo sexa sensor exterior ou interior
//const char* mqttNomeCliente = "emeelh/transmitancia/SensorExterior_";
//const char* mqttCanalParede = "emeehl/transmitancia/SensorExterior/Parede";
//const char* mqttCanalAmbiente = "emeehl/transmitancia/SensorExterior/Ambiente";
const char* mqttNomeCliente = "emeelh/transmitancia/SensorInterior_";
const char* mqttCanalParede = "emeehl/transmitancia/SensorInterior/Parede";
const char* mqttCanalAmbiente = "emeehl/transmitancia/SensorInterior/Ambiente";

//Sensor DS18b20:
//---------------------------------------------------------------
OneWire parede(ONE_WIRE_BUS_PAREDE);
OneWire ambiente(ONE_WIRE_BUS_AMBIENTE);

DallasTemperature sensParede(&parede);
DallasTemperature sensAmbiente(&ambiente);

int tempoLectura = 10000; // Periodo temporal para cada nova lectura (en ms)

void setup() {
  Serial.begin(9600);
  conectarWiFi();
  mqttClient.setServer(mqttServer, 1883);
//  mqttClient.setCallback(callback);
  pinMode(ONE_WIRE_BUS_PAREDE, INPUT_PULLUP);  //Con este parámetro evitamos a 
  pinMode(ONE_WIRE_BUS_AMBIENTE, INPUT_PULLUP);//resistencia de pullup no sensor
  sensParede.begin();
  sensAmbiente.begin();
}

void loop() {
  // Obtén temperaturas e publícaas como texto no monitor serie
  String tempsParede = obtenTempsTexto(sensParede);
  String tempsAmbiente = obtenTempsTexto(sensAmbiente);
  Serial.print("Parede: "); Serial.println(tempsParede);
  Serial.print("Ambiente: "); Serial.println(tempsAmbiente);

  // Conéctase aos servidor mosquitto e ...
  if(!mqttClient.connected()) {
    Serial.print("Conectando co servidor MQTT... ");
    mqttClient.connect(mqttNomeCliente);
    Serial.println(mqttClient.state());
  }
  // publica as temperaturas para os sensore de parede e ambiente
  else {
    Serial.println("MQTT ok");
    char mqttTempsParede[tempsParede.length()+1];
    char mqttTempsAmbiente[tempsAmbiente.length()+1];
    tempsParede.toCharArray(mqttTempsParede, tempsParede.length()+1);
    tempsAmbiente.toCharArray(mqttTempsAmbiente, tempsAmbiente.length()+1);
    mqttClient.publish(mqttCanalParede, mqttTempsParede);
    mqttClient.publish(mqttCanalAmbiente, mqttTempsAmbiente);
  }

  delay(tempoLectura);
}

void conectarWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Esperando pola WiFi ");
  int contador = 0;
  while(WiFi.status() != WL_CONNECTED and contador < MAX_INTENTOS) {
    contador++;
    delay(500);
    Serial.print(".");
    //Serial.print(WiFi.status());
  }
  Serial.println("");
  if(contador < MAX_INTENTOS) {
    Serial.print("Conectado á WiFi coa IP: "); Serial.println(WiFi.localIP());
  }
  else {
    Serial.println("Non se puido conectar á WiFi");
  }

}

//void callback(char* tema, byte* mensaxe, unsigned int lonxitude) {
//  Serial.print("Mensaxe mqtt ["); Serial.print(tema); Serial.print("]");
//  String saida = "";
//  for(int i=0; i<lonxitude; i++) {
//    saida += mensaxe[i];
//  }
//  Serial.println(saida);
//}

//void reconnect() {
//  while(!mqttClient.connected()) {
//    Serial.print("Tentando conexión MQTT...");
//    if(mqttClient.connect("Client Raspi ESP8266")) {
//      Serial.println("Conectado ao servidor MQTT");
//      mqttClient.subscribe("transmitancia");
//    }
//    else {
//      Serial.print("Fallou a conexión, rc=");
//      Serial.print(mqttClient.state());
//      Serial.println(" inténtase novamente en 5 segundos");
//      delay(5000);
//    }
//  }
//}

float calculaMedia(float *temp, int nTemps) {
  float suma = 0;
  for(int i=0; i<nTemps; i++) {
    suma += temp[i];
  }
  return(suma/nTemps);
}

String obtenTempsTexto(DallasTemperature sensor) {
  int8_t nSens = -1;
  String tempsTexto = "";
  sensor.requestTemperatures();
  nSens = sensor.getDeviceCount();
  for(int s=0; s<nSens; s++) {
    float t = sensor.getTempCByIndex(s);
    if(t >= -55 && t <= 125) {  //Rango do sensor: -55 ºC a +125 ºC
      tempsTexto += t; tempsTexto += "; ";
    }
  }
  return(tempsTexto);
}



