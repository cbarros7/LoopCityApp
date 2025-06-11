// Ya no necesitamos process.env. Las variables se inyectan directamente en el ámbito global del script.
// Remueve o comenta las siguientes líneas si estaban:
// var appUsername = process.env.MONGO_APP_USERNAME;
// var appPassword = process.env.MONGO_APP_PASSWORD;
// var appDatabase = process.env.MONGO_APP_DATABASE;

// Estas variables ahora se asumen que están definidas por el argumento --eval
// (Puedes dejar la comprobación por si acaso, aunque con --eval debería ser más robusto)
if (typeof appUsername === 'undefined' || typeof appPassword === 'undefined' || typeof appDatabase === 'undefined') {
    print("Error: appUsername, appPassword, o appDatabase no están definidos. Asegúrese de que se pasen correctamente.");
    quit(1);
}

// Cambia al contexto de la base de datos de la aplicación
db = db.getSiblingDB(appDatabase);

print(`Creando usuario '${appUsername}' para la base de datos '${appDatabase}'...`);

// Crea el usuario de la aplicación con permisos de lectura/escritura en la base de datos de la aplicación
db.createUser(
  {
    user: appUsername,
    pwd: appPassword,
    roles: [
      { role: "readWrite", db: appDatabase }
    ]
  },
  { w: "majority" } // Espera confirmación de la mayoría de los nodos para la creación del usuario
);

print("Usuario de aplicación creado exitosamente.");

// Crea las colecciones y sus índices si no existen
print(`Creando/Asegurando colecciones e índices en '${appDatabase}'...`);

// Colección para datos crudos de Meetup
db.createCollection("raw_events_meetup");
db.raw_events_meetup.createIndex( { "event_id": 1 }, { unique: true, background: true } );
db.raw_events_meetup.createIndex( { "scraped_at": -1 }, { background: true } );
print("Colección 'raw_events_meetup' y sus índices asegurados.");

// Colección para IDs de Eventbrite
db.createCollection("eventbrite_ids");
db.eventbrite_ids.createIndex( { "eventbrite_id": 1 }, { unique: true, background: true } );
db.eventbrite_ids.createIndex( { "status": 1, "scraped_at": -1 }, { background: true } );
db.eventbrite_ids.createIndex( { "status": 1, "retries": 1 }, { background: true } );
print("Colección 'eventbrite_ids' y sus índices asegurados.");

print("Configuración de colecciones e índices completada.");