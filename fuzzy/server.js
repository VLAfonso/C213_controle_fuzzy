// server.js

const express = require('express');
const http = require('http');
const socketio = require('socket.io');
const mqtt = require('mqtt');
const path = require('path');

const app = express();
const server = http.createServer(app);
// Inicializa o Socket.IO para comunicação em tempo real
const io = socketio(server);

// --- Configurações MQTT ---
const BROKER_URL = 'mqtt://test.mosquitto.org';
const TOPIC_TEMP_REQUEST = 'datacenter/fuzzy/temp/request';
const TOPIC_ALERT_REQUEST = 'datacenter/fuzzy/alert/request';
const TOPIC_SETPOINT_REQUEST = 'datacenter/fuzzy/control/setpoint/request';

// Conecta ao broker MQTT
const client = mqtt.connect(BROKER_URL);

// Assina os tópicos relevantes
client.on('connect', () => {
    console.log('Conectado ao Broker MQTT');
    client.subscribe([TOPIC_TEMP_REQUEST, TOPIC_ALERT_REQUEST], (err) => {
        if (!err) {
            console.log('Inscrito nos tópicos de temperatura e alerta.');
        }
    });
});

// Lida com as mensagens MQTT recebidas
client.on('message', (topic, message) => {
    const payload = message.toString();
    console.log(`[MQTT] Tópico: ${topic}, Payload: ${payload}`);

    if (topic === TOPIC_TEMP_REQUEST) {
        const [tempStr, erroStr, potenciaStr] = payload.split(';');
        const data = {
            timestamp: new Date().toLocaleTimeString(),
            temperatura: parseFloat(tempStr),
            erro: parseFloat(erroStr),
            potencia: parseFloat(potenciaStr) 
        };
        // Envia os dados de temperatura/erro
        io.sockets.emit('mqttData', data); 
    } else if (topic === TOPIC_ALERT_REQUEST) {
        // Envia os dados de alerta 
        io.sockets.emit('mqttAlert', payload);
    }
});

// --- Configurações Servidor Web (Express) ---

app.use(express.static(path.join(__dirname, 'public')));
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Lida com a conexão de clientes web via Socket.IO
io.on('connection', (socket) => {
    console.log('Novo cliente web conectado!');

    //Listener para receber comandos do Front
    socket.on('sendSetpoint', (newSetpoint) => {
        console.log(`[Socket.IO] Comando recebido: Novo Setpoint: ${newSetpoint}`);
        
        //Publica o comando via MQTT para o cliente Python
        client.publish(TOPIC_SETPOINT_REQUEST, newSetpoint.toString(), { qos: 1 }, (error) => {
            if (error) {
                console.error("Erro ao publicar setpoint via MQTT:", error);
            } else {
                console.log(`Setpoint ${newSetpoint} publicado com sucesso.`);
            }
        });
    });

    socket.on('disconnect', () => {
        console.log('Cliente web desconectado.');
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Servidor rodando em http://localhost:${PORT}`);
});