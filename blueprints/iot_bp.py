from flask import Blueprint, render_template, jsonify, session, redirect, url_for, request
from db import conexao
import globals_iot

iot_bp = Blueprint('iot_bp', __name__)

# decorador para proteger rotas
def login_required(route):
    def wrapper(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login_bp.login'))
        return route(*args, **kwargs)
    wrapper.__name__ = route.__name__
    return wrapper

@iot_bp.route('/home')
@login_required
def home():
    return render_template('home.html')

@iot_bp.route('/tempo_real')
@login_required
def tempo_real():
    values = {"temperatura": globals_iot.temperatura, "umidade": globals_iot.umidade}
    return render_template("tr.html", values=values)

@iot_bp.route('/publicar')
@login_required
def publicar():
    return render_template('publicar.html', led_status=globals_iot.led_status)

@iot_bp.route('/publicar_mensagem', methods=['POST'])
@login_required
def publicar_mensagem():
    request_data = request.get_json()
    topic = request_data.get('topic', '/aula_flask/led')
    mensagem = request_data.get('mensagem', '0')
    globals_iot.led_status = int(mensagem)
    globals_iot.mqtt_client.publicar(topic, mensagem)
    return jsonify({'led_status': globals_iot.led_status})

@iot_bp.route('/listar_dados_sensor')
@login_required
def listar_dados_sensor():
    return jsonify({
        'temperatura': globals_iot.temperatura,
        'umidade': globals_iot.umidade,
        'ultima_atualizacao': globals_iot.ultima_atualizacao
    })