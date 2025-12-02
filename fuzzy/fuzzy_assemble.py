import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import time
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
import sys
import json

tol_erro = 2
passo_erro = 0.1
passo_var_erro = 0.01

is_ready_to_start = False #flag para a lógica fuzzy
global set_point
global temp_atual_global
global temp_externa_global
global carga_termica_global
global erro_anterior_global

temp_atual_global = 32
temp_externa_global = 25
carga_termica_global = 40
set_point = 22
erro_anterior_global = temp_atual_global - set_point

# Motor de Inferência Mamdani
def mandani():
    # Definindo universo de discurso das variáveis de entrada e saída
    erro = ctrl.Antecedent(np.arange(-16, 16+passo_erro, passo_erro), 'erro')
    variacao_erro =ctrl.Antecedent(np.arange(-2*tol_erro, 2*tol_erro+passo_var_erro, passo_var_erro), 'variacao_erro')
    sistema_crac =ctrl.Consequent(np.arange(0, 101, 1), 'sistema_crac')

    # Função de pertinência do erro
    erro['MN'] = fuzz.trapmf(erro.universe, [-16, -16, -2*tol_erro,-tol_erro])
    erro['PN'] = fuzz.trimf(erro.universe, [-2*tol_erro,-tol_erro,0])
    erro['ZE'] = fuzz.trimf(erro.universe, [-tol_erro, 0, tol_erro])
    erro['PP'] = fuzz.trimf(erro.universe, [0, tol_erro, 2*tol_erro])
    erro['MP'] = fuzz.trapmf(erro.universe,[tol_erro, 2*tol_erro, 16+passo_erro,16+passo_erro])

    # Função de pertinência da variação do erro
    variacao_erro['MN'] = fuzz.trapmf(variacao_erro.universe, [-2*tol_erro, -2*tol_erro, -2*tol_erro/10,-tol_erro/10])
    variacao_erro['PN'] = fuzz.trimf(variacao_erro.universe, [-2*tol_erro/10,-tol_erro/10,0])
    variacao_erro['ZE'] = fuzz.trimf(variacao_erro.universe, [-tol_erro/10, 0, tol_erro/10])
    variacao_erro['PP'] = fuzz.trimf(variacao_erro.universe, [0, tol_erro/10, 2*tol_erro/10])
    variacao_erro['MP'] = fuzz.trapmf(variacao_erro.universe,[tol_erro/10, 2*tol_erro/10, 2*tol_erro+passo_var_erro,2*tol_erro+passo_var_erro])

    # Função de pertinência do sistema CRAC
    sistema_crac['MB'] = fuzz.trimf(sistema_crac.universe, [0,0,25])
    sistema_crac['B'] = fuzz.trimf(sistema_crac.universe, [0,25,50])
    sistema_crac['M'] = fuzz.trimf(sistema_crac.universe, [25, 50, 75])
    sistema_crac['A'] = fuzz.trimf(sistema_crac.universe, [50, 75, 101])
    sistema_crac['MA'] = fuzz.trimf(sistema_crac.universe, [75, 101, 101])

    # Regras (mantive suas 25 regras)
    regras = []
    regras.append(ctrl.Rule(erro['MN']& variacao_erro['MN'], sistema_crac['MB']))
    regras.append(ctrl.Rule(erro['PN']& variacao_erro['MN'], sistema_crac['MB']))
    regras.append(ctrl.Rule(erro['ZE']& variacao_erro['MN'], sistema_crac['B']))
    regras.append(ctrl.Rule(erro['PP']& variacao_erro['MN'], sistema_crac['M']))
    regras.append(ctrl.Rule(erro['MP']& variacao_erro['MN'], sistema_crac['M']))
    regras.append(ctrl.Rule(erro['MN']& variacao_erro['PN'], sistema_crac['MB']))
    regras.append(ctrl.Rule(erro['PN']& variacao_erro['PN'], sistema_crac['B']))
    regras.append(ctrl.Rule(erro['ZE']& variacao_erro['PN'], sistema_crac['B']))
    regras.append(ctrl.Rule(erro['PP']& variacao_erro['PN'], sistema_crac['M']))
    regras.append(ctrl.Rule(erro['MP']& variacao_erro['PN'], sistema_crac['A']))
    regras.append(ctrl.Rule(erro['MN']& variacao_erro['ZE'], sistema_crac['MB']))
    regras.append(ctrl.Rule(erro['PN']& variacao_erro['ZE'], sistema_crac['B']))
    regras.append(ctrl.Rule(erro['ZE']& variacao_erro['ZE'], sistema_crac['B']))
    regras.append(ctrl.Rule(erro['PP']& variacao_erro['ZE'], sistema_crac['M']))
    regras.append(ctrl.Rule(erro['MP']& variacao_erro['ZE'], sistema_crac['A']))
    regras.append(ctrl.Rule(erro['MN']& variacao_erro['PP'], sistema_crac['B']))
    regras.append(ctrl.Rule(erro['PN']& variacao_erro['PP'], sistema_crac['M']))
    regras.append(ctrl.Rule(erro['ZE']& variacao_erro['PP'], sistema_crac['M']))
    regras.append(ctrl.Rule(erro['PP']& variacao_erro['PP'], sistema_crac['A']))
    regras.append(ctrl.Rule(erro['MP']& variacao_erro['PP'], sistema_crac['MA']))
    regras.append(ctrl.Rule(erro['MN']& variacao_erro['MP'], sistema_crac['M']))
    regras.append(ctrl.Rule(erro['PN']& variacao_erro['MP'], sistema_crac['M']))
    regras.append(ctrl.Rule(erro['ZE']& variacao_erro['MP'], sistema_crac['A']))
    regras.append(ctrl.Rule(erro['PP']& variacao_erro['MP'], sistema_crac['MA']))
    regras.append(ctrl.Rule(erro['MP']& variacao_erro['MP'], sistema_crac['MA']))

    sistema_crac_ctrl = ctrl.ControlSystem(regras)
    potencia_sim = ctrl.ControlSystemSimulation(sistema_crac_ctrl)

    return erro, variacao_erro, sistema_crac, potencia_sim

def mostrar_graficos(erro, variacao_erro, sistema_crac):
    try:
        erro.view()
        variacao_erro.view()
        sistema_crac.view()
    except Exception as e:
        print("Não foi possível exibir os gráficos (ambiente headless?):", e)

def sistema_miso(erro_val, variacao_erro_val, potencia_sim):
    # usa o objeto ControlSystemSimulation passado (potencia_sim)
    potencia_sim.input['erro'] = erro_val
    potencia_sim.input['variacao_erro'] = variacao_erro_val
    potencia_sim.compute()
    return float(potencia_sim.output['sistema_crac'])

def funcao_transferencia(temp_atual, potencia, carga_termica, temp_externa):
    return 0.9*temp_atual - 0.08*potencia + 0.05*carga_termica + 0.02*temp_externa + 3.5

def controlador_fuzzy(set_point, temp_atual, carga_termica, temp_externa, erro_anterior, potencia_hist, potencia_sim, client=None):
    # potencia_hist -> vetor/array com histórico (para armazenar)
    # potencia_sim -> ControlSystemSimulation (objeto fuzzy)
    erro_atual = temp_atual - set_point
    variacao_erro = erro_atual - erro_anterior
    
    potencia_atual = sistema_miso(erro_atual, variacao_erro, potencia_sim)

    nova_temp = funcao_transferencia(temp_atual, potencia_atual, carga_termica, temp_externa)

    return nova_temp, erro_atual, potencia_atual

def fuzzy_loop(f_sim):
    global temp_atual_global
    global temp_externa_global
    global carga_termica_global
    global erro_anterior_global
    global set_point

    while True:
        temp_anterior = temp_atual_global

        temp_atual_global, erro_atual, potencia_atual = controlador_fuzzy(
            set_point,
            temp_atual_global,
            carga_termica_global,
            temp_externa_global,
            erro_anterior_global,
            [], 
            f_sim
        )

        payload = f"{temp_atual_global:.2f};{erro_atual:.2f};{potencia_atual:.2f}"
        client.publish("datacenter/fuzzy/temp/request", payload)

        # alertas
        if temp_atual_global > 26 or temp_atual_global < 18:
            client.publish("datacenter/fuzzy/alert/request", "1")

        if (temp_atual_global - temp_anterior) >= 1:
            client.publish("datacenter/fuzzy/alert/request", "3")

        erro_anterior_global = erro_atual
        print("Nova medida:", payload)

        time.sleep(5)

def main():
    print("Chamou a main")
    f_erro, f_var_erro, f_sistema, f_sim = mandani()
    fuzzy_loop(f_sim)

#---------------MQTT-----------------#
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_ALERT = "datacenter/fuzzy/alert/#"
TOPIC_CTRL = "datacenter/fuzzy/control/#"
TOPIC_TEMP = "datacenter/fuzzy/temp/#"
TOPIC_START = "datacenter/fuzzy/start/#"

def on_connect(client_obj, userdata, flags, rc):
    print("Conectado com código:", rc)
    client_obj.subscribe(TOPIC_ALERT)
    client_obj.subscribe(TOPIC_CTRL)
    client_obj.subscribe(TOPIC_TEMP)
    client_obj.subscribe(TOPIC_START)

    client_obj.publish("datacenter/fuzzy/start/request", "1")

def on_message(client_obj, userdata, msg):
    global is_ready_to_start
    global set_point
    print(f"[RECEBIDO] {msg.topic}: {msg.payload.decode()}")

    lista = msg.topic.split("/")
    mensagem = msg.payload.decode().split(";")
    print(mensagem)

    #if(len(mensagem)>=3):
    if(lista[2] == ("start") and lista[3] == ("response")):
        print("start response")
        is_ready_to_start = True

    if(lista[2] == ("alert") and lista[3] == ("response")):
        print("alert response")
    
    if(lista[2] == ("control") and lista[3] == ("response")):
        print("control response")
    
    if(lista[2] == ("control") and lista[3] == ("setpoint") and lista[4] == ("request")):
        try:
            new_set_point = float(mensagem[0])
            new_temp_atual = float(mensagem[1])
            new_temp_externa = float(mensagem[2])
            new_carga_termica = float(mensagem[3])

            # Atualizar valores globais
            set_point = new_set_point
            temp_atual_global = new_temp_atual
            temp_externa_global = new_temp_externa
            carga_termica_global = new_carga_termica
            erro_anterior_global = temp_atual_global - set_point

            print(f"[UPDATE] Novo Setpoint = {set_point}")
            print(f"[UPDATE] Temp Atual = {temp_atual_global}")
            print(f"[UPDATE] Temp Externa = {temp_externa_global}")
            print(f"[UPDATE] Carga Térmica = {carga_termica_global}")

            client.publish("datacenter/fuzzy/control/setpoint/response", "1")

        except Exception as e:
            print("Erro ao atualizar setpoint:", e)

    if(lista[2] == ("temp") and lista[3] == ("response")):
        print("temp response")

# Inicializando conexão do cliente Mqtt
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60) 
except Exception:
    print("Não foi possivel conectar ao MQTT...")
    print("Encerrando...")
    sys.exit()    

# Iniciando Loop 
try:
    client.loop_start()

    while not is_ready_to_start:
        time.sleep(0.1) 

    try:
        main()
    except KeyboardInterrupt:
        print("Encerrando...")
        client.loop_stop()

except KeyboardInterrupt:
    print("Encerrando...")
