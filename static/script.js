// formata números para exibição
function formata_numero(valor, casasDecimais = 1) {
    return parseFloat(valor).toFixed(casasDecimais);
}

// Atualiza o status do LED na interface
function atualiza_led(estado) {
    const modo_led = document.getElementById('status-led');
    if (!modo_led) return;
    if (estado === 1) {
        modo_led.innerHTML = '🟢 LED LIGADO';
    } else {
        modo_led.innerHTML = '🔴 LED DESLIGADO';
    }
}

function atualiza_dados() {
    const valor_temperatura = document.getElementById('valor_temperatura');
    const valor_umidade = document.getElementById('valor_umidade');

    // guarda os valores atuais
    const tempAtual = valor_temperatura ? valor_temperatura.textContent : null;
    const umidAtual = valor_umidade ? valor_umidade.textContent : null;

    // envia comando para solicitar atualização ao ESP
    fetch('/publicar_mensagem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: '/aula_flask/atualizar', mensagem: '1' })
    })
        .then(response => response.json())
        .then(() => {
            // função para tentar buscar os dados até que mudem
            const tentarAtualizar = () => {
                fetch('/listar_dados_sensores')
                    .then(response => response.json())
                    .then(data => {
                        const novaTemp = formata_numero(data.temperatura);
                        const novaUmid = formata_numero(data.umidade);

                        // se os dados mudaram, atualiza a tela
                        if (novaTemp !== tempAtual || novaUmid !== umidAtual) {
                            if (valor_temperatura) valor_temperatura.textContent = novaTemp;
                            if (valor_umidade) valor_umidade.textContent = novaUmid;
                        } else {
                            // se não mudou, tenta novamente em 500ms
                            setTimeout(tentarAtualizar, 500);
                        }
                    })
                    .catch(err => console.log('Erro ao buscar dados: ' + err.mensagem));
            };

            // inicia a tentativa de atualização
            tentarAtualizar();
        })
        .catch(err => console.log('Erro ao enviar comando: ' + err.mensagem));
}

// publica comando LED
function publicar_led(estado) {

    const ligar_botao = document.getElementById('ligar_botao');
    const desligar_botao = document.getElementById('desligar_botao');

    // desabilitar botões durante a requisição
    if (ligar_botao) ligar_botao.disabled = true;
    if (desligar_botao) desligar_botao.disabled = true;

    fetch('/publicar_mensagem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: '/aula_flask/led', mensagem: estado.toString() })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na resposta da rede');
            }
            return response.json();
        })
        .then(data => {
            atualiza_led(data.led_status);
        })
        .catch(err => {
            console.log('Erro ao publicar: ' + err.mensagem, 'error');
        })
        .finally(() => {
            // Reabilitar botões
            if (ligar_botao) ligar_botao.disabled = false;
            if (desligar_botao) desligar_botao.disabled = false;
        });
}

// inicialização baseada na página
document.addEventListener('DOMContentLoaded', function () {
    // verificar se estamos na página de controle do LED
    if (document.getElementById('ligar_botao') && document.getElementById('desligar_botao')) {
        console.log('Página de controle do LED carregada', 'info');
    }

    // verificar se estamos na página de tempo real
    if (document.getElementById('valor_temperatura') && document.getElementById('valor_umidade')) {
        console.log('Página de tempo real carregada', 'info');
        atualiza_dados();
    }
});
