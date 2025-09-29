from flask import Flask, render_template, request, redirect, send_from_directory, jsonify, abort, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user, UserMixin
from forms import RegisterForm, LoginForm
import os
from datetime import datetime

# Configuración básica
app = Flask(__name__)

# SECRET_KEY (usar variable de entorno en producción)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'cambia_esta_clave_en_produccion'

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

# Inicializar extensiones
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Fan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    photo = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

# Crear tablas de forma idempotente durante la importación
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

# Loader para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

# Utilidades
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Rutas de utilidad
@app.route("/health")
def health_check():
    return jsonify(status="ok", message="Happy Fans está saludable"), 200

@app.route("/")
def home():
    return render_template("home.html") if os.path.exists(os.path.join('templates','home.html')) else f"¡Hola, {current_user.name if current_user.is_authenticated else 'Cache'}! Happy Fans está conectado a la base de datos."

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash('Ese correo ya está registrado.', 'error')
            return render_template('register.html', form=form)
        u = User(email=form.email.data.lower(), name=form.name.data)
        u.set_password(form.password.data)
        try:
            db.session.add(u)
            db.session.commit()
            flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creando usuario: {e}")
            flash('Error creando cuenta.', 'error')
    return render_template('register.html', form=form)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data.lower()).first()
        if u and u.check_password(form.password.data):
            login_user(u)
            flash('Bienvenido.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        flash('Email o contraseña incorrectos.', 'error')
    return render_template('login.html', form=form)

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.', 'success')
    return redirect(url_for('home'))

# Mostrar formulario (restringido a usuarios autenticados)
@app.route("/form")
@login_required
def fan_form():
    return render_template("fan_form.html")

# Procesar formulario con validación y manejo seguro de archivos
@app.route("/submit", methods=["POST"])
@login_required
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

    new_fan = Fan(name=name, message=message, photo=filename, user_id=current_user.id if current_user.is_authenticated else None)
    try:
        db.session.add(new_fan)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error guardando Fan: {e}")
        abort(500, description="Error interno al guardar datos.")

    return redirect("/form")

# Mostrar lista de fans ordenados por fecha (pública)
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
