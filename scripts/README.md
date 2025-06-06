## Cómo usar manage_stack_up.sh:
Este script te permitirá levantar:

    Todo el stack (full).
    Una parte específica del stack (kafka).
    Varias partes del stack (backend_api mongodb1).


### Para subir todo el stack: 
./scripts/manage_stack_up.sh full

### Para subir solo Kafka: 
./scripts/manage_stack_up.sh kafka

### Para subir backend_api, mongodb1 y redis-master
./scripts/manage_stack_up.sh backend_api mongodb1 redis-master



## El Script para Bajar el Stack (manage_stack_down.sh)

Este script te permitirá bajar:

    Todo el stack (full).
    Una parte específica del stack (kafka).
    Varias partes del stack (backend_api mongodb1).

Cómo usar manage_stack_down.sh:

    Para bajar todo el stack (preservando datos):
    Bash

./scripts/manage_stack_down.sh full

Para detener solo Kafka:
Bash

./scripts/manage_stack_down.sh kafka

Para detener backend_api y mongodb1:
Bash

./scripts/manage_stack_down.sh backend_api mongodb1




Para subir todo el stack sin limpiar el caché (comportamiento por defecto):
Bash

./scripts/manage_stack_up.sh full

Para subir todo el stack y limpiar el caché de todas las imágenes antes:
Bash

./scripts/manage_stack_up.sh full --clean-cache
# O la forma corta:
# ./scripts/manage_stack_up.sh full -c

Para subir solo Kafka sin limpiar el caché:
Bash

./scripts/manage_stack_up.sh kafka

Para subir backend_api y mongodb1, limpiando el caché de esas imágenes antes:
Bash

    ./scripts/manage_stack_up.sh backend_api mongodb1 --clean-cache
    # O la forma corta:
    # ./scripts/manage_stack_up.sh backend_api mongodb1 -c





### Generate certs. 
 ./scripts/generate_certs.sh     