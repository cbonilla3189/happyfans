from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Crear instancia de la aplicación Flask
app = Flask(__name__)

# Configurar la URI de la base de datos desde la variable de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Definir el modelo Fan
class Fan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=False)

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()
    print("✅ Base de datos inicializada correctamente con la tabla 'Fan'.")
