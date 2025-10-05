from flask_mqtt import Mqtt

mqtt_client = None  # será inicializado no app principal
temperatura = 25.0
umidade = 60.0
led_status = 0
ultima_atualizacao = 0
