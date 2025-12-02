import paho.mqtt.client as mqtt
import time
import sys
import json

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_ALERT = "datacenter/fuzzy/alert/#"
TOPIC_CTRL = "datacenter/fuzzy/control/#"
TOPIC_TEMP = "datacenter/fuzzy/temp/#"
TOPIC_START = "datacenter/fuzzy/start/#"


def on_connect(client, userdata, flags, rc):
    print("Conectado com código:", rc)
    client.subscribe(TOPIC_ALERT)
    client.subscribe(TOPIC_CTRL)
    client.subscribe(TOPIC_TEMP)
    client.subscribe(TOPIC_START)


def on_message(client, userdata, msg):
    print(f"[RECEBIDO] {msg.topic}: {msg.payload.decode()}")

    print(msg.topic+" "+str(msg.payload.decode()))
    lista = msg.topic.split("/")
    mensagem = msg.payload.decode().split(";")
    print(mensagem)

#-----------------------------------------ALERTA DE CRITICIDADE----------------------------------------------------------#
    if(lista[2] == ("start") and lista[3] == ("request")):
        #Limites críticos foram excedidos
        print("START")
        try:
            client.publish("datacenter/fuzzy/start/response", "1")
        except:
            client.publish("datacenter/fuzzy/start/response", "2") #ERRO

#-----------------------------------------ALERTA DE CRITICIDADE----------------------------------------------------------#
    if(lista[2] == ("alert") and lista[3] == ("request")):
        #Limites críticos foram excedidos
        print("TEMPERATURA CRÍTICA")
        try:
            client.publish("datacenter/fuzzy/alert/response", "1")
        except:
            client.publish("datacenter/fuzzy/alert/response", "2") #ERRO
#-----------------------------------------CONTROLE----------------------------------------------------------#
    if(lista[2] == ("control") and lista[3] == ("request")):
        #dados de controle
        print("CONTROLE")
        try:
            client.publish("datacenter/fuzzy/control/response", "1")
        except:
            client.publish("datacenter/fuzzy/control/response", "2") #ERRO

#-----------------------------------------TEMPERATURA----------------------------------------------------------#
    if(lista[2] == ("temp") and lista[3] == ("request")):
        #dados de controle
        print("TEMPERATURA")
        try:
            client.publish("datacenter/fuzzy/temp/response", "1")
        except:
            client.publish("datacenter/fuzzy/temp/response", "2") #ERRO

#Inicializando conexão do cliente Mqtt
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60) 

except:
    print("Não foi possivel conectar ao MQTT...")
    print("Encerrando...")
    sys.exit()    

#Iniciando Loop até haver falha na conexão do BD
try:
    client.loop_forever()
except KeyboardInterrupt:  #preSSionar Crtl + C para sair
    print("Encerrando...")