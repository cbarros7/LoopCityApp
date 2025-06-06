import os
import json
import time
from confluent_kafka import Consumer, KafkaException, KafkaError
from src.kafka_manager import KafkaManager # Asegúrate de que esta ruta sea correcta
import logging
import sys

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_consumer(group_id, topics):
    """
    Ejecuta un consumidor de Kafka.
    :param group_id: ID del grupo de consumidores.
    :param topics: Lista de topics a los que suscribirse.
    """
    # El ambiente se puede pasar como argumento a este script también
    # o confiar en la variable de entorno KAFKA_ENV.
    env_from_args = sys.argv[1] if len(sys.argv) > 1 else None
    os.environ['KAFKA_ENV'] = env_from_args if env_from_args else os.getenv("KAFKA_ENV", "development") # Fallback a .env o 'development'

    try:
        kafka_manager = KafkaManager(env=os.environ['KAFKA_ENV']) # Aseguramos que KafkaManager sepa el ambiente
        
        # Obtener la configuración del consumidor del KafkaManager
        consumer_conf = kafka_manager.get_consumer_config(group_id=group_id)
        consumer = Consumer(consumer_conf)
        
        logging.info(f"Consumidor de Kafka inicializado para {kafka_manager.env} con brokers: {consumer_conf['bootstrap.servers']}")
        logging.info(f"Grupo de consumidor: {group_id}")
        logging.info(f"Subscribiéndose a topics: {topics}")

        # Suscribirse a los topics
        consumer.subscribe(topics)

        # Bucle de consumo
        try:
            while True:
                msg = consumer.poll(timeout=1.0) # Espera un mensaje por 1 segundo

                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError.PARTITION_EOF:
                        # Fin de la partición (no es un error real, solo indica que no hay más mensajes por ahora)
                        logging.info(f"%% End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                    elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                        logging.error(f"Error de Kafka: Topic o partición desconocida: {msg.error()}")
                    elif msg.error():
                        logging.error(f"Error de consumidor: {msg.error()}")
                else:
                    # Mensaje válido recibido
                    logging.info(f"Recibido mensaje de topic '{msg.topic()}' [partición {msg.partition()}] @ offset {msg.offset()}:")
                    logging.info(f"  Key: {msg.key().decode('utf-8') if msg.key() else 'N/A'}")
                    logging.info(f"  Value: {msg.value().decode('utf-8')}")

        except KeyboardInterrupt:
            logging.info("Interrupción por usuario. Deteniendo consumidor.")
        finally:
            # Cerrar limpiamente el consumidor
            consumer.close()
            logging.info("Consumidor cerrado.")

    except Exception as e:
        logging.critical(f"Fallo crítico al iniciar o usar el consumidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Define el ID del grupo de consumidor y los topics a los que se suscribirá
    # Puedes obtener estos del entorno o de un archivo de configuración si es más complejo.
    
    # Para desarrollo, puedes usar un grupo simple y los topics que esperas.
    # Asegúrate de que 'raw_events', 'raw_weather', 'raw_places' existan o se creen.
    # El 'kafka-topic-initializer' debería encargarse de crearlos.
    CONSUMER_GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "my-ingestor-group")
    TOPICS_TO_SUBSCRIBE = os.getenv("KAFKA_TOPICS_TO_SUBSCRIBE", "raw_events,raw_weather,raw_places").split(',')
    
    run_consumer(CONSUMER_GROUP_ID, TOPICS_TO_SUBSCRIBE)