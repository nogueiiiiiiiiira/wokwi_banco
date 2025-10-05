from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mqtt import Mqtt
import time
import json
import mysql.connector

app = Flask(__name__)

def conexao():
    host = "localhost"
    user = "root"
    password = ""
    database = "iot_flask"
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        if conn.is_connected():
            return conn
    except mysql.connector.Error as err:
        print(f"[ERRO MYSQL] {err}")
        return None

app.config['MQTT_BROKER_URL'] = 'mqtt-dashboard.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 60
app.config['MQTT_TLS_ENABLED'] = False

mqtt_client = Mqtt(app)

temperatura = 25.0
umidade = 60.0
led_status = 0
last_update = time.time()
topic_subscribe = "/aula_flask/#"

@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html', erro=False)

@app.route('/validar_usuario', methods=['POST'])
def validar_usuario():
    usuario = request.form['usuario']
    password = request.form['password']
    conn = conexao()
    if conn is None:
        return "Erro ao conectar ao banco de dados", 500
    cursor = conn.cursor()
    cursor.execute("SELECT senha FROM usuarios WHERE email = %s", (usuario,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and user[0] == password:
        return redirect(url_for('home'))
    else:
        return render_template('login.html', erro=True)

@app.route('/adicionar_usuario', methods=['GET', 'POST'])
def adicionar_usuario():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            return "Dados inválidos", 400
        conn = conexao()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (email, senha) VALUES (%s, %s)", (email, password))
            conn.commit()
            cursor.close()
            conn.close()
        return redirect(url_for('listar_usuarios'))
    else:
        return render_template('adicionar_usuario.html')


@app.route('/deletar_usuario', methods=['GET', 'POST'])
def deletar_usuario():
    email = request.form.get('email') or request.args.get('email')
    if not email:
        return "Usuário inválido", 400
    conn = conexao()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE email = %s", (email,))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('listar_usuarios'))

@app.route('/usuarios')
def listar_usuarios():
    conn = conexao()
    usuarios = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email FROM usuarios ORDER BY id ASC")
        usuarios = [{'id': row[0], 'email': row[1]} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
    return render_template("usuarios.html", usuarios=usuarios)

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    conn = conexao()
    if conn is None:
        return "Erro ao conectar ao banco de dados", 500
    cursor = conn.cursor()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            return "Dados inválidos", 400
        cursor.execute("UPDATE usuarios SET email = %s, senha = %s WHERE id = %s", (email, password, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('listar_usuarios'))
    else:
        cursor.execute("SELECT id, email FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        if usuario:
            return render_template('editar_usuario.html', usuario={'id': usuario[0], 'email': usuario[1]})
        else:
            return "Usuário não encontrado", 404

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/tempo_real')
def tempo_real():
    global temperatura, umidade
    values = {"temperatura": temperatura, "umidade": umidade}
    return render_template("tr.html", values=values)

@app.route('/publish')
def publish():
    global led_status
    return render_template('publish.html', led_status=led_status)

@app.route('/publish_message', methods=['POST'])
def publish_message():
    global led_status
    request_data = request.get_json()
    topic = request_data.get('topic', '/aula_flask/led')
    message = request_data.get('message', '0')
    led_status = int(message)
    mqtt_client.publish(topic, message)
    return jsonify({'led_status': led_status})

@app.route('/get_sensor_data')
def get_sensor_data():
    global temperatura, umidade, last_update
    return jsonify({'temperatura': temperatura, 'umidade': umidade, 'last_update': last_update})

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print('[MQTT] Conectado com sucesso ao broker!')
        mqtt_client.subscribe(topic_subscribe)
        print(f'[MQTT] Inscrito no tópico: {topic_subscribe}')
    else:
        print('[MQTT] Falha na conexão. Código:', rc)

@mqtt_client.on_disconnect()
def handle_disconnect(client, userdata, rc):
    print("[MQTT] Desconectado do broker")

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    global temperatura, umidade, last_update
    try:
        payload = message.payload.decode()
        data = json.loads(payload)
        if data.get("sensor") == "/aula_flask/temperatura":
            temperatura = float(data["valor"])
            tipo = "temperatura"
        elif data.get("sensor") == "/aula_flask/umidade":
            umidade = float(data["valor"])
            tipo = "umidade"
        else:
            return
        last_update = time.time()
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

@app.route('/historico')
def historico():
    conn = conexao()
    if conn is None:
        return "Erro ao conectar ao banco de dados", 500
    cursor = conn.cursor()
    cursor.execute("SELECT tipo, valor, atualizado_em FROM sensores ORDER BY atualizado_em DESC LIMIT 20")
    dados = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('historico.html', dados=dados)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
