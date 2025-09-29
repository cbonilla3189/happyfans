from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import time

# Esperar unos segundos para asegurar que la base de datos esté lista
time.sleep(5)

# Verificar que DATABASE_URL esté disponible
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("❌ DATABASE_URL no está definida. Render aún no la ha inyectado.")
    sys.exit(1)

# Crear instancia de la aplicación Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Definir el modelo Fan
class Fan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=False)

# Crear las tablas en la base de datos
try:
    with app.app_context():
        db.create_all()
        print("✅ Base de datos inicializada correctamente con la tabla 'Fan'.")
except Exception as e:
    print(f"❌ Error al inicializar la base de datos: {e}")
    sys.exit(1)
