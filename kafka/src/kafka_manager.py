import os
import yaml
import time
from datetime import datetime
from confluent_kafka.admin import AdminClient, NewTopic, ConfigResource, ConfigSource
from confluent_kafka import KafkaException, KafkaError
from confluent_kafka import Producer, Consumer # Importar para los getters de config
import logging
import sys # Para leer argumentos de la línea de comandos

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KafkaManager:
    _instance = None

    def __new__(cls, env=None, from_cmd_args=False):
        if cls._instance is None:
            cls._instance = super(KafkaManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, env=None, from_cmd_args=False):
        if self._initialized:
            return

        # Prioridad de ambiente: Argumento de línea de comandos > Variable de entorno > Default 'development'
        if from_cmd_args and len(sys.argv) > 1:
            self.env = sys.argv[1]
        elif env:
            self.env = env
        else:
            self.env = os.getenv("KAFKA_ENV", "development")

        self._load_config()
        self.admin_client = self._create_admin_client()
        self._initialized = True
        logging.info(f"KafkaManager inicializado para el ambiente: {self.env}")

    def _load_config(self):
        """Carga la configuración de Kafka y los topics desde los archivos YAML."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, '..', 'config', 'kafka_config.yaml')
        topics_path = os.path.join(current_dir, '..', 'config', 'topics.yaml')

        try:
            with open(config_path, 'r') as f:
                full_config = yaml.safe_load(f)
            self.config = full_config.get(self.env)
            if not self.config:
                raise ValueError(f"Configuración no encontrada para el ambiente: {self.env}")

            with open(topics_path, 'r') as f:
                self.topic_definitions = yaml.safe_load(f).get('topics', {})

            # Ajuste dinámico del replication_factor según el ambiente
            for topic_name, details in self.topic_definitions.items():
                if self.env == "development":
                    details['replication_factor'] = 1 # Para desarrollo, 1 es suficiente
                elif self.env in ["staging", "production"]:
                    # Para staging/prod, forzar un factor de replicación de 3 o más
                    if details.get('replication_factor', 0) < 3:
                        details['replication_factor'] = 3
                        logging.info(f"Ajustando replication_factor para '{topic_name}' a 3 en ambiente {self.env}.")

        except FileNotFoundError as e:
            logging.error(f"Error: Archivo de configuración no encontrado: {e}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error al parsear archivo YAML: {e}")
            raise
        except Exception as e:
            logging.error(f"Error inesperado al cargar la configuración: {e}")
            raise

    def _create_admin_client(self):
        """Crea y devuelve una instancia de AdminClient con la configuración del ambiente."""
        conf = {
            'bootstrap.servers': self.config['brokers'],
            'client.id': self.config['client_id'],
            'security.protocol': self.config.get('security_protocol', 'PLAINTEXT'),
        }
        # Añadir configuraciones de seguridad adicionales
        if conf['security.protocol'] == 'SSL':
            conf['ssl.ca.location'] = self.config.get('ssl_ca_location')
            conf['ssl.cert.location'] = self.config.get('ssl_cert_location')
            conf['ssl.key.location'] = self.config.get('ssl_key.location') # Corregido de ssl_key_location
        elif conf['security.protocol'] in ['SASL_SSL', 'SASL_PLAINTEXT']:
            conf['sasl.mechanism'] = self.config.get('sasl_mechanism')
            conf['sasl.username'] = self.config.get('sasl_username')
            conf['sasl.password'] = self.config.get('sasl_password')
            # Solo añadir propiedades SSL si el protocolo es SASL_SSL
            if conf['security.protocol'] == 'SASL_SSL':
                if 'ssl.ca.location' in self.config:
                    conf['ssl.ca.location'] = self.config['ssl_ca_location']
                if 'ssl.cert.location' in self.config:
                    conf['ssl.cert.location'] = self.config['ssl_cert_location']
                    conf['ssl.key.location'] = self.config['ssl_key.location']

        return AdminClient(conf)

    def wait_for_brokers_ready(self):
        """
        Espera activamente a que los brokers de Kafka estén listos usando el AdminClient.
        """
        logging.info(f"Esperando a que los brokers de Kafka en {self.config['brokers']} estén listos...")
        retries = 0
        max_retries = 60 # Intentos de 1 segundo, hasta 1 minuto
        while retries < max_retries:
            try:
                # list_topics(timeout) intenta obtener metadata. Un timeout bajo es suficiente.
                metadata = self.admin_client.list_topics(timeout=1.0)
                if metadata.brokers:
                    logging.info("Brokers de Kafka listos y conectados.")
                    return True
                else:
                    logging.warning(f"No se encontraron brokers en la metadata. Reintentando... ({retries+1}/{max_retries})")
            except KafkaException as e:
                # BROKER_NOT_AVAILABLE es común si los brokers no están listos
                if e.args[0].code() == KafkaError.BROKER_NOT_AVAILABLE:
                    logging.warning(f"Broker no disponible: {e.args[0].str()}. Reintentando... ({retries+1}/{max_retries})")
                else:
                    logging.error(f"Error inesperado al verificar brokers: {e}. Reintentando... ({retries+1}/{max_retries})")
            except Exception as e:
                logging.error(f"Excepción general al esperar brokers: {e}. Reintentando... ({retries+1}/{max_retries})")

            time.sleep(1)
            retries += 1
        
        logging.error(f"Fallo al conectar con los brokers de Kafka después de {max_retries} intentos.")
        raise RuntimeError("Brokers de Kafka no disponibles.")

    def create_topics(self):
        """
        Crea los topics definidos en topics.yaml. Idempotente y con reintentos.
        """
        self.wait_for_brokers_ready() # Asegurarse de que los brokers estén listos primero

        logging.info(f"Iniciando la creación/verificación de topics para el ambiente {self.env}...")
        
        new_topics = []
        for topic_name, details in self.topic_definitions.items():
            num_partitions = details['partitions']
            replication_factor = details['replication_factor'] # Ya ajustado para el ambiente
            topic_configs = details.get('configs', {})
            
            new_topics.append(NewTopic(topic_name, num_partitions, replication_factor, topic_configs))

        if not new_topics:
            logging.info("No hay topics definidos para crear.")
            return

        retries = 0
        while retries <= self.config['max_retries_create_topics']:
            try:
                futures = self.admin_client.create_topics(new_topics, request_timeout=self.config['topic_creation_timeout_ms'] / 1000) # Timeout en segundos

                all_succeeded = True
                for topic, future in futures.items():
                    try:
                        future.result() # Espera a que la operación se complete
                        logging.info(f"Topic '{topic}' creado o ya existente con éxito.")
                    except KafkaException as e:
                        if e.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS:
                            logging.info(f"Topic '{topic}' ya existe.")
                        else:
                            logging.error(f"Fallo al crear o verificar el topic '{topic}': {e}")
                            all_succeeded = False
                    except Exception as e:
                        logging.error(f"Excepción inesperada para el topic '{topic}': {e}")
                        all_succeeded = False
                
                if all_succeeded:
                    logging.info("Todos los topics han sido creados o verificados exitosamente.")
                    return

            except KafkaException as e:
                logging.error(f"Fallo general al intentar crear topics: {e}. Reintentando... ({retries+1}/{self.config['max_retries_create_topics']})")
                all_succeeded = False
            except Exception as e:
                logging.error(f"Error inesperado durante la creación de topics: {e}. Reintentando... ({retries+1}/{self.config['max_retries_create_topics']})")
                all_succeeded = False
            
            if not all_succeeded and retries < self.config['max_retries_create_topics']:
                time.sleep(self.config['retry_backoff_ms'] / 1000)
            retries += 1
        
        logging.error(f"Fallo al crear o verificar topics después de {self.config['max_retries_create_topics']} intentos.")
        raise RuntimeError("No se pudieron crear/verificar todos los topics requeridos.")

    def get_producer_config(self):
        """Devuelve la configuración completa para un KafkaProducer, incluyendo la idempotencia."""
        conf = {
            'bootstrap.servers': self.config['brokers'],
            'client.id': self.config['client_id'],
            'security.protocol': self.config.get('security_protocol', 'PLAINTEXT'),
        }
        # Añadir propiedades del productor (incluyendo idempotencia)
        producer_props = self.config.get('producer_properties', {})
        conf.update(producer_props)

        # Añadir configuraciones de seguridad adicionales si existen
        if conf['security.protocol'] == 'SSL':
            conf['ssl.ca.location'] = self.config.get('ssl_ca_location')
            conf['ssl.cert.location'] = self.config.get('ssl_cert_location')
            conf['ssl.key.location'] = self.config.get('ssl_key.location')
        elif conf['security.protocol'] in ['SASL_SSL', 'SASL_PLAINTEXT']:
            conf['sasl.mechanism'] = self.config.get('sasl_mechanism')
            conf['sasl.username'] = self.config.get('sasl_username')
            conf['sasl.password'] = self.config.get('sasl_password')
            if 'ssl.ca.location' in self.config:
                conf['ssl.ca.location'] = self.config['ssl_ca_location']
            if 'ssl.cert.location' in self.config:
                conf['ssl.cert.location'] = self.config['ssl_cert_location']
                conf['ssl.key.location'] = self.config['ssl_key.location']
        return conf

    def get_consumer_config(self, group_id):
        """Devuelve la configuración necesaria para un KafkaConsumer."""
        conf = {
            'bootstrap.servers': self.config['brokers'],
            'client.id': self.config['client_id'], # Puedes usar un client_id diferente para consumidores
            'group.id': group_id,
            'security.protocol': self.config.get('security.protocol', 'PLAINTEXT'),
            'auto.offset.reset': 'earliest', # O 'latest' según la necesidad
            # 'enable.auto.commit': 'true', # Default en True
            # 'auto.commit.interval.ms': '5000' # Default 5 segundos
        }
        # Añadir configuraciones de seguridad adicionales
        if conf['security.protocol'] == 'SSL':
            conf['ssl.ca.location'] = self.config.get('ssl_ca_location')
            conf['ssl.cert.location'] = self.config.get('ssl_cert_location')
            conf['ssl.key.location'] = self.config.get('ssl_key.location')
        elif conf['security.protocol'] in ['SASL_SSL', 'SASL_PLAINTEXT']:
            conf['sasl.mechanism'] = self.config.get('sasl_mechanism')
            conf['sasl.username'] = self.config.get('sasl_username')
            conf['sasl.password'] = self.config.get('sasl_password')
            if 'ssl.ca.location' in self.config:
                conf['ssl.ca.location'] = self.config['ssl_ca_location']
            if 'ssl.cert.location' in self.config:
                conf['ssl.cert.location'] = self.config['ssl_cert_location']
                conf['ssl.key.location'] = self.config['ssl_key.location']
        return conf

# Este bloque se ejecutará cuando el script sea llamado directamente (ej. por entrypoint.sh)
if __name__ == "__main__":
    try:
        # Pasa from_cmd_args=True para que el constructor intente leer sys.argv[1]
        logging.info("Iniciando proceso de inicialización de topics con KafkaManager.")
        kafka_manager = KafkaManager(from_cmd_args=True)
        kafka_manager.create_topics()
        logging.info("Proceso de inicialización de topics completado exitosamente.")
    except Exception as e:
        logging.critical(f"Fallo crítico en el proceso de inicialización de topics: {e}")
        sys.exit(1) # Salir con código de error si falla la creación de topics críticos