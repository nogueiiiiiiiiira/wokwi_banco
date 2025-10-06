from flask import Flask, redirect
from flask_mqtt import Mqtt
import config
import globals_iot

# blueprints
from blueprints.login_bp import login_bp
from blueprints.iot_bp import iot_bp
from blueprints.datas_bp import datas_bp

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = config.SECRET_KEY

# inicializa MQTT e salva no módulo global
globals_iot.mqtt_client = Mqtt(app)

# variáveis IoT globais
globals_iot.temperatura = 25.0
globals_iot.umidade = 60.0
globals_iot.led_status = 0
globals_iot.ultima_atualizacao = 0
globals_iot.topic_subscribe = "/aula_flask/#"

# registrar Blueprints
app.register_blueprint(login_bp)
app.register_blueprint(iot_bp)
app.register_blueprint(datas_bp)

# rota principal
@app.route('/')
def index():
    return redirect('/login')


# MQTT
@globals_iot.mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print('[MQTT] Conectado com sucesso ao broker!')
        globals_iot.mqtt_client.subscribe(globals_iot.topic_subscribe)
        print(f'[MQTT] Inscrito no tópico: {globals_iot.topic_subscribe}')
    else:
        print('[MQTT] Falha na conexão. Código:', rc)


@globals_iot.mqtt_client.on_disconnect()
def handle_disconnect(client, userdata, rc):
    print("[MQTT] Desconectado do broker")


@globals_iot.mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    import json, time
    from db import conexao

    try:
        payload = message.payload.decode()
        data = json.loads(payload)

        if data.get("sensor") == "/aula_flask/temperatura":
            globals_iot.temperatura = float(data["valor"])
            tipo = "temperatura"
        elif data.get("sensor") == "/aula_flask/umidade":
            globals_iot.umidade = float(data["valor"])
            tipo = "umidade"
        else:
            return

        globals_iot.ultima_atualizacao = time.time()

        conn = conexao()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sensores (tipo, valor) VALUES (%s, %s)", (tipo, data["valor"]))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"[MQTT] Dados salvos no banco - {tipo}: {data['valor']}")
        else:
            print("[ERRO MYSQL] Falha ao conectar ao banco.")

    except Exception as e:
        print(f"[MQTT] Erro ao processar mensagem: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
