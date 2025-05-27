-- Este script crearía tu keyspace y tablas, y un usuario para la aplicación
-- Crea un usuario con los permisos adecuados
CREATE USER IF NOT EXISTS '${CASSANDRA_APP_USERNAME}' WITH PASSWORD '${CASSANDRA_APP_PASSWORD}' NOSUPERUSER;
-- Otorga permisos al usuario de aplicación en el keyspace de tu aplicación
-- Ejemplo:
-- CREATE KEYSPACE IF NOT EXISTS loop_city_events WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 3};
-- GRANT ALL PERMISSIONS ON KEYSPACE loop_city_events TO loopcityapp;