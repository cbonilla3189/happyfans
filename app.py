from flask import Flask, render_template, request, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Configuración de la aplicación
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///happyfans.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Carpeta para guardar fotos subidas
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Inicializar base de datos
db = SQLAlchemy(app)

# Modelo Fan
class Fan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    photo = db.Column(db.String(200), nullable=True)  # Ruta de la foto

# Ruta principal
@app.route("/")
def home():
    return "¡Hola, Carlos! Happy Fans está conectado a la base de datos."

# Mostrar formulario
@app.route("/form")
def fan_form():
    return render_template("fan_form.html")

# Procesar formulario
@app.route("/submit", methods=["POST"])
def submit_fan():
    name = request.form["name"]
    message = request.form["message"]
    photo_file = request.files.get("photo")
    photo_path = None

    if photo_file and photo_file.filename != "":
        filename = secure_filename(photo_file.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo_file.save(photo_path)

    new_fan = Fan(name=name, message=message, photo=filename if photo_path else None)
    db.session.add(new_fan)
    db.session.commit()
    return redirect("/form")

# Mostrar lista de fans ordenados por fecha
@app.route("/fans")
def show_fans():
    fans = Fan.query.order_by(Fan.timestamp.desc()).all()
    return render_template("fan_list.html", fans=fans)

# Servir archivos subidos
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Punto de entrada
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
