from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileAllowed

class RegisterForm(FlaskForm):
    name = StringField('Nombre', validators=[Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField('Confirmar contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Entrar')
