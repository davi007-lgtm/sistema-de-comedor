from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import datetime
import os
import locale
from extensions import db, login_manager, migrate

# Configurar el locale en español
try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')
    except:
        pass  # Si no se puede configurar el locale, se usa el predeterminado

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cafeteria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Importar modelos después de inicializar db
from models import Usuario, Estudiante, Asistencia, Menu, Configuracion

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Registrar blueprints
from routes.auth import auth_bp
from routes.students import students_bp
from routes.attendance import attendance_bp
from routes.menus import menus_bp
from routes.reports import reports_bp
from routes.admin import admin_bp
from routes.main import main_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(students_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(menus_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True) 