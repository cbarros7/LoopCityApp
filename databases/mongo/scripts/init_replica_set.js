// ./databases/mongo/scripts/create_app_user.js
// Se ejecuta con el usuario admin

const appUsername = process.env.MONGO_APP_USERNAME;
const appPassword = process.env.MONGO_APP_PASSWORD;
const appDatabase = process.env.MONGO_APP_DATABASE || 'your_application_db'; // Asegúrate de que este nombre coincida con tu config

// Cambia a la base de datos de tu aplicación
db = db.getSiblingDB(appDatabase);

// Verifica si el usuario ya existe para evitar errores en reinicios
if (!db.getUser(appUsername)) {
    print(`Creando usuario de aplicación '${appUsername}' en la base de datos '${appDatabase}'...`);
    db.createUser(
        {
            user: appUsername,
            pwd: appPassword,
            roles: [
                { role: "readWrite", db: appDatabase } // Rol de lectura/escritura en tu base de datos de aplicación
                // Puedes añadir más roles si necesitas: "readAnyDatabase", "dbAdmin" etc.
            ]
        }
    );
    print("Usuario de aplicación creado exitosamente.");
} else {
    print(`Usuario de aplicación '${appUsername}' ya existe.`);
}