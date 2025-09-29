from flask import Flask, render_template, request, redirect, send_from_directory, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Configuración básica
app = Flask(__name__)

# Configurar la URI de la base de datos con fallback a SQLite local
db_url = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(os.getcwd(), 'happyfans.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de subida de archivos
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Inicializar base de datos
db = SQLAlchemy(app)

# Modelo Fan
class Fan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    photo = db.Column(db.String(200), nullable=True)

# Inicializar tablas de forma idempotente durante la importación
try:
    db_url_check = app.config.get('SQLALCHEMY_DATABASE_URI')
    if db_url_check:
        with app.app_context():
            db.create_all()
            app.logger.info("Base de datos inicializada correctamente (import-time).")
    else:
        app.logger.warning("DATABASE_URL no presente en import; la BD se creará al primer request.")
except Exception as e:
    app.logger.error(f"Error al inicializar la base de datos en import: {e}")

# Rutas de utilidad
@app.route("/health")
def health_check():
    return jsonify(status="ok", message="Happy Fans está saludable"), 200

@app.route("/")
def home():
    return "¡Hola, Carlos! Happy Fans está conectado a la base de datos."

# Validadores de archivos
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Mostrar formulario
@app.route("/form")
def fan_form():
    return render_template("fan_form.html")

# Procesar formulario con validación y manejo seguro de archivos
@app.route("/submit", methods=["POST"])
def submit_fan():
    name = (request.form.get("name") or "").strip()
    message = (request.form.get("message") or "").strip()

    if not name or not message:
        abort(400, description="Nombre y mensaje son obligatorios.")

    photo_file = request.files.get("photo")
    filename = None

    if photo_file and photo_file.filename:
        if not allowed_file(photo_file.filename):
            abort(400, description="Tipo de archivo no permitido.")
        filename = secure_filename(photo_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            photo_file.save(file_path)
        except Exception as e:
            app.logger.error(f"Error guardando archivo: {e}")
            abort(500, description="Error al guardar la imagen.")

    new_fan = Fan(name=name, message=message, photo=filename)
    try:
        db.session.add(new_fan)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error guardando Fan: {e}")
        abort(500, description="Error interno al guardar datos.")

    return redirect("/form")

# Mostrar lista de fans ordenados por fecha
@app.route("/fans")
def show_fans():
    fans = Fan.query.order_by(Fan.timestamp.desc()).all()
    return render_template("fan_list.html", fans=fans)

# Servir archivos subidos
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Manejo de errores simples
@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e.description)), 400

@app.errorhandler(500)
def server_error(e):
    return jsonify(error="Error interno del servidor"), 500

# Ejecutar localmente
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
