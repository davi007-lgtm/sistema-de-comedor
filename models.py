from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    rol = db.Column(db.String(20), nullable=False)  # admin, personal, monitor
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    
    id = db.Column(db.Integer, primary_key=True)
    identificador = db.Column(db.String(20), unique=True, nullable=False)  # Código QR
    nombre = db.Column(db.String(100), nullable=False)
    curso = db.Column(db.String(50), nullable=False)
    tipo_estudiante = db.Column(db.String(20), nullable=False)  # becado, pagado
    estado = db.Column(db.Boolean, default=True)  # True = activo, False = inactivo
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    asistencias = db.relationship('Asistencia', backref='estudiante', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'identificador': self.identificador,
            'nombre': self.nombre,
            'curso': self.curso,
            'tipo_estudiante': self.tipo_estudiante,
            'estado': self.estado
        }

class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    hora = db.Column(db.Time, nullable=False, default=datetime.utcnow().time)
    tipo = db.Column(db.String(20), nullable=False, default='almuerzo')  # desayuno, almuerzo, cena
    metodo_registro = db.Column(db.String(20), default='manual')  # manual, QR, tarjeta
    registrado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observaciones = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'estudiante_id': self.estudiante_id,
            'fecha': self.fecha.isoformat(),
            'hora': self.hora.isoformat(),
            'tipo': self.tipo,
            'metodo_registro': self.metodo_registro,
            'registrado_por': self.registrado_por,
            'observaciones': self.observaciones
        }

class Menu(db.Model):
    __tablename__ = 'menus'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    comida_principal = db.Column(db.String(200), nullable=False)
    guarnicion = db.Column(db.String(200))
    postre = db.Column(db.String(200))
    calorias = db.Column(db.Integer)
    notas = db.Column(db.Text)

class Configuracion(db.Model):
    __tablename__ = 'configuraciones'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.String(200))
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 