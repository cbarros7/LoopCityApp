from redis.sentinel import Sentinel
import os

# Obtener las variables de entorno
sentinel_hosts_str = os.getenv('REDIS_SENTINELS')
master_name = os.getenv('REDIS_MASTER_NAME')
password = os.getenv('REDIS_PASSWORD') # <--- Lee la contraseña

# Parsear la cadena de hosts de los Sentinels
sentinels_list = []
if sentinel_hosts_str:
    for s_host_port in sentinel_hosts_str.split(','):
        host, port = s_host_port.strip().split(':')
        sentinels_list.append((host, int(port)))

# Inicializar el Sentinel con la contraseña
sentinel = Sentinel(sentinels_list, socket_connect_timeout=0.5, password=password)

# Obtener el cliente maestro (para escrituras)
# La contraseña se pasa automáticamente a la instancia master_for
redis_master_client = sentinel.master_for(master_name)

# Obtener el cliente esclavo (opcional, para lecturas)
# La contraseña se pasa automáticamente a la instancia slave_for
# redis_slave_client = sentinel.slave_for(master_name)