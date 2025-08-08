from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Fan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=False)

@app.route("/")
def home():
    return "¡Hola, Carlos! Happy Fans está conectado a la base de datos."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
