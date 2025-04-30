from extensions import db
from datetime import datetime

class Asistencia(db.Model):
    __tablename__ = 'asistencias'

    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False)  # 'desayuno', 'almuerzo', 'cena'
    registrado_por = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relaciones
    estudiante = db.relationship('Estudiante', backref=db.backref('asistencias', lazy=True))
    registrador = db.relationship('User', backref=db.backref('asistencias_registradas', lazy=True))

    def __repr__(self):
        return f'<Asistencia {self.estudiante.nombre} - {self.fecha}>'

    def to_dict(self):
        return {
            'id': self.id,
            'estudiante_id': self.estudiante_id,
            'estudiante_nombre': self.estudiante.nombre if self.estudiante else None,
            'fecha': self.fecha.isoformat(),
            'tipo': self.tipo,
            'registrado_por': self.registrador.nombre if self.registrador else None
        } 