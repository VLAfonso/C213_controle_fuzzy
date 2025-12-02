# C213 - Projeto Sistema de Controle Fuzzy
Repositório destinado ao projeto Sistema de Controle Fuzzy MISO para Refrigeração em Centros de Dados da disciplina C213 - Sistemas Embarcados.

## :pencil: Descrição
O presente projeto tem como objetivo desenvolver um sistema de controle fuzzy MISO (Multiple Input, Single Output) para controle de temperatura em um centro de dados. 

## :book: Documentação
A documentação do projeto pode ser encontrada na pasta [`docs`](./docs) e possui:
    - Relatório de Design - justifica o design de funções de pertinência, explica a base de regras desenvolvida, analisa a estratégia de controle implementada e apresenta diagramas de fluxo do algoritmo.
    - Análise de Resultados - analisa os resultados obtidos, realiza testes de validação do sistema, analisa resposta ante a diferentes cenários, compara com controladores tradicionais e avalia a robustez e estabilidade.

## :gear: Execução
1. Clonar o repositório
```bash
git clone https://github.com/VLAfonso/C213_controle_fuzzy.git
cd C213_controle_fuzzy
```
2. Iniciar Conexão
Primeiro é necessário iniciar o servidor com o node:
```bash
cd fuzzy
node server.js
```
Em um novo terminal, dentro da pasta `fuzzy` é necessário iniciar a conexão MQTT:
```bash
python fuzzy_assemble.py
```
3. Abrir interface
Abrir o arquivo [`fuzzy/public/trabalho.html`](./fuzzy/public/trabalho.html).
> :pushpin: **Notas:** É necessário ter o [Node.js](https://nodejs.org/) instalado.

## :busts_in_silhouette: Desenvolvedoras 
[Lanna Correia e Silva](https://github.com/LannaCeS)  
[Lucas Lima Gadbem](https://github.com/LucasLimaGadbem)  
[Virgínia Letícia Afonso](https://github.com/VLAfonso)

## :scroll: Licença
Este projeto está licenciado sob a MIT License.