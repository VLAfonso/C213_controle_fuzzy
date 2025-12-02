const MAX_DATA_POINTS = 20; // Limita o número de pontos no gráfico

// Conecta ao Socket.IO no servidor Node.js
const socket = io();

// Elementos HTML para dados atuais
const currentTempEl = document.getElementById('current-temp');
const currentErrorEl = document.getElementById('current-error');
const lastUpdateEl = document.getElementById('last-update');
const lastAlertEl = document.getElementById('last-alert');
const currentPowerEl = document.getElementById('current-power');
const powerBarEl = document.getElementById('power-bar');
const alertCardEl = document.getElementById('alert-card');
const alertStatusEl = document.getElementById('alert-status');

// --- Inicialização dos Gráficos (Chart.js) ---

//Configuração base dos dados do gráfico
const chartData = {
    labels: [], // Timestamps
    datasets: [{
        label: 'Temperatura (°C)',
        data: [],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
        fill: false
    }]
};

// Gráfico de Temperatura
const tempCtx = document.getElementById('tempChart').getContext('2d');
const tempChart = new Chart(tempCtx, {
    type: 'line',
    data: chartData,
    options: {
        responsive: true,
        scales: {
            y: {
                title: { display: true, text: 'Temperatura (°C)' }
            }
        }
    }
});

// Gráfico de Erro
const errorData = {
    labels: [], // Timestamps
    datasets: [{
        label: 'Erro (Temp. Atual - Set Point)',
        data: [],
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1,
        fill: false
    }]
};
const errorCtx = document.getElementById('errorChart').getContext('2d');
const errorChart = new Chart(errorCtx, {
    type: 'line',
    data: errorData,
    options: {
        responsive: true,
        scales: {
            y: {
                title: { display: true, text: 'Erro' }
            }
        }
    }
});

// --- Recebimento de Dados do Socket.IO ---

// Recebe dados de temperatura e erro do servidor Node.js
socket.on('mqttData', (data) => {
    // 1. Atualiza os cards de dados atuais
    currentTempEl.textContent = data.temperatura.toFixed(2);
    currentErrorEl.textContent = data.erro.toFixed(2);
    lastUpdateEl.textContent = data.timestamp;

    //Atualiza o valor de Potência
    currentPowerEl.textContent = data.potencia.toFixed(2);
    
    //Atualiza a barra do "medidor" de Potência
    const percentage = Math.min(100, Math.max(0, data.potencia)); // Limita entre 0 e 100
    powerBarEl.style.width = `${percentage}%`;
    powerBarEl.textContent = `${percentage.toFixed(0)}%`;

    // Atualiza os dados dos gráficos
    tempChart.data.labels.push(data.timestamp);
    tempChart.data.datasets[0].data.push(data.temperatura);
    
    errorChart.data.labels.push(data.timestamp);
    errorChart.data.datasets[0].data.push(data.erro);

    // Remove o ponto mais antigo se exceder o limite
    if (tempChart.data.labels.length > MAX_DATA_POINTS) {
        tempChart.data.labels.shift();
        tempChart.data.datasets[0].data.shift();
    }
    if (errorChart.data.labels.length > MAX_DATA_POINTS) {
        errorChart.data.labels.shift();
        errorChart.data.datasets[0].data.shift();
    }

    // Redesenha os gráficos
    tempChart.update();
    errorChart.update();
});

// Recebe alertas do servidor Node.js
socket.on('mqttAlert', (payload) => {
    let alertMessage = '';
    // Alerta
    if (payload === '1') {
        alertMessage = `CRÍTICO: TEMPERATURA CRÍTICA EXCEDIDA!`;
        alertCardEl.style.backgroundColor = '#fff1f0'; // Cor de fundo para crítico
        alertCardEl.style.borderColor = '#f5222d';
    } else if (payload === '3') {
        alertMessage = `ATENÇÃO: MUDANÇA BRUSCA DETECTADA!`;
        alertCardEl.style.backgroundColor = '#fffbe6'; // Cor de fundo para atenção
        alertCardEl.style.borderColor = '#faad14';
    } else {
        alertMessage = `Alerta Desconhecido: ${payload}`;
    }
    
    alertStatusEl.textContent = alertMessage;

    // Auto-limpa o alerta de mudança brusca após 10 segundos
    if (payload === '3') {
        setTimeout(() => {
            if (alertStatusEl.textContent.includes("MUDANÇA BRUSCA")) {
                alertStatusEl.textContent = "Tudo normal";
                alertCardEl.style.backgroundColor = '#e6f7ff';
                alertCardEl.style.borderColor = '#1890ff';
            }
        }, 10000);
    }
    
    if (payload !== '1') {
        // Se não for o alerta 1 (crítico), restaura o estado normal
        if (!alertMessage.includes("MUDANÇA BRUSCA")) {
            alertCardEl.style.backgroundColor = '#e6f7ff';
            alertCardEl.style.borderColor = '#1890ff';
        }
    }
});