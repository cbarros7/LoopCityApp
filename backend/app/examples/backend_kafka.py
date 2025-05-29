from confluent_kafka import Producer, Consumer, KafkaException
import json
import asyncio

# --- Configuración para Kafka PLAINTEXT (sin SSL/TLS ni SASL) ---
# Si tu FastAPI está en el mismo Docker Compose network que Kafka:
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
# Si tu FastAPI está en tu máquina host y Kafka expone 9092:9092 en docker-compose:
# KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

TOPIC_NAME = "test-topic" # Usa el mismo topic que usaste para las pruebas

# --- PRODUCER ---
def delivery_report(err, msg):
    """Callback para confirmar la entrega del mensaje."""
    if err is not None:
        print(f"Error de entrega del mensaje: {err}")
    else:
        print(f"Mensaje producido a {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

def get_kafka_producer():
    """Configura y retorna una instancia del productor de Kafka."""
    # Propiedades del productor para PLAINTEXT
    producer_conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        # No se necesitan propiedades ssl.* o sasl.* para PLAINTEXT sin autenticación
    }
    return Producer(producer_conf)

async def send_message_to_kafka(message_data: dict):
    """Envía un mensaje JSON a Kafka."""
    producer = get_kafka_producer()
    try:
        # La función produce es síncrona en confluent-kafka-python,
        # pero es seguro usarla en un contexto asíncrono si el I/O es gestionado por la librería.
        # Para FastAPI, puedes envolver esto en un executor si necesitas un alto rendimiento asíncrono.
        producer.produce(
            TOPIC_NAME,
            key=str(message_data.get("id")).encode('utf-8'), # Opcional: clave del mensaje
            value=json.dumps(message_data).encode('utf-8'), # Mensaje en formato JSON
            callback=delivery_report
        )
        # Llama a poll para invocar callbacks de entrega (como delivery_report)
        # y forzar el envío de mensajes pendientes.
        producer.poll(0) # No espera, solo procesa eventos pendientes
        producer.flush() # Espera a que todos los mensajes sean entregados
        return True
    except KafkaException as e:
        print(f"Error al producir mensaje: {e}")
        return False

# --- CONSUMER ---
def get_kafka_consumer():
    """Configura y retorna una instancia del consumidor de Kafka."""
    consumer_conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'my_fastapi_consumer_group', # ID de grupo de consumidor
        'auto.offset.reset': 'earliest', # Empieza a leer desde el principio si no hay offsets guardados
        # No se necesitan propiedades ssl.* o sasl.* para PLAINTEXT sin autenticación
    }
    return Consumer(consumer_conf)

async def consume_messages_from_kafka():
    """Consume mensajes de Kafka de forma continua."""
    consumer = get_kafka_consumer()
    consumer.subscribe([TOPIC_NAME])

    print(f"Consumidor iniciado para el topic: {TOPIC_NAME}")
    try:
        while True:
            # poll es síncrono. En un entorno FastAPI real, esto
            # se ejecutaría en un thread o proceso separado para no bloquear el bucle de eventos.
            msg = consumer.poll(timeout=1.0) # Espera hasta 1 segundo por un mensaje

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    # Fin de la partición (normal si no hay mensajes nuevos)
                    continue
                else:
                    print(f"Error del consumidor: {msg.error()}")
                    break
            else:
                print(f"Mensaje recibido: {msg.value.decode('utf-8')} (Key: {msg.key().decode('utf-8') if msg.key() else 'N/A'})")
                # Aquí puedes procesar el mensaje, guardarlo en una base de datos, etc.
    except Exception as e:
        print(f"Excepción en el consumidor: {e}")
    finally:
        consumer.close()

# --- Integración con FastAPI (ejemplo conceptual) ---
# En tu archivo principal de FastAPI (ej. main.py):

# from fastapi import FastAPI
# app = FastAPI()

# @app.on_event("startup")
# async def startup_event():
#     # Inicia el consumidor en un thread/proceso separado para no bloquear FastAPI
#     # Esto es una simplificación, para producción usarías BackgroundTasks o un worker
#     asyncio.create_task(consume_messages_from_kafka())

# @app.post("/send-kafka-message/")
# async def send_message(message: dict):
#     success = await send_message_to_kafka(message)
#     if success:
#         return {"status": "Message sent to Kafka"}
#     else:
#         return {"status": "Failed to send message to Kafka"}

# # Para ejecutar esto en desarrollo:
# # uvicorn main:app --reload