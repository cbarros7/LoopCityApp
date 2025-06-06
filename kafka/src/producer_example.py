import os
import json
import time
from confluent_kafka import Producer
from src.kafka_manager import KafkaManager
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def delivery_report(err, msg):
    """Callback llamado una vez que un mensaje ha sido entregado o ha fallado."""
    if err is not None:
        logging.error(f"Fallo en la entrega del mensaje: {err}")
    else:
        logging.info(f"Mensaje entregado a topic '{msg.topic()}' [partición {msg.partition()}] @ offset {msg.offset()}")

def run_producer():
    # El ambiente se puede pasar como argumento a este script también
    # o confiar en la variable de entorno KAFKA_ENV.
    # Aquí, se lo pasamos al KafkaManager para que elija la configuración correcta.
    env_from_args = sys.argv[1] if len(sys.argv) > 1 else None
    os.environ['KAFKA_ENV'] = env_from_args if env_from_args else os.getenv("KAFKA_ENV", "development") # Fallback a .env o 'development'

    try:
        kafka_manager = KafkaManager(env=os.environ['KAFKA_ENV']) # Aseguramos que KafkaManager sepa el ambiente
        
        producer_conf = kafka_manager.get_producer_config()
        producer = Producer(producer_conf)
        logging.info(f"Productor de Kafka inicializado para {kafka_manager.env} con brokers: {producer_conf['bootstrap.servers']}")
        logging.info(f"Configuración de idempotencia: enable.idempotence={producer_conf.get('enable.idempotence')}, acks={producer_conf.get('acks')}, retries={producer_conf.get('retries')}")

        messages_to_send = [
            {"metadata": {"source_api": "ticketmaster", "query_type": "events_by_city", "timestamp": str(datetime.now())}, "data": {"id": "TM001", "name": "Concierto A"}},
            {"metadata": {"source_api": "eventbrite", "query_type": "events_search", "timestamp": str(datetime.now())}, "data": {"event_id": "EB002", "title": "Charla B"}},
            {"metadata": {"source_api": "openweather", "query_type": "current_weather", "timestamp": str(datetime.now())}, "data": {"city": "Madrid", "temp": 25}},
        ]

        for i, msg_data in enumerate(messages_to_send):
            # Lógica para determinar el topic basada en la estructura de datos
            if msg_data["metadata"]["source_api"] == "openweather":
                topic = "raw_weather"
            elif msg_data["metadata"]["source_type"] == "places": # Ejemplo para un futuro mensaje de lugares
                topic = "raw_places"
            else: # Por defecto a eventos
                topic = "raw_events" 
            
            key = f"message_{i}-{int(time.time())}" # Clave para asegurar buena distribución en particiones

            try:
                producer.produce(topic, key=key.encode('utf-8'), value=json.dumps(msg_data).encode('utf-8'), callback=delivery_report)
                producer.poll(0) 
                time.sleep(0.5) # Pausa entre mensajes para simular tráfico real
            except BufferError:
                logging.warning(f"Cola de productor llena, esperando... ({len(producer)} mensajes pendientes)")
                producer.poll(1)
            except Exception as e:
                logging.error(f"Error al producir mensaje: {e}")

        logging.info("Flushing productor... esperando entrega de mensajes pendientes.")
        producer.flush(30)
        logging.info("Productor finalizado.")

    except Exception as e:
        logging.critical(f"Fallo crítico al iniciar o usar el productor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_producer()