from app import app, db
from models import Usuario, Estudiante, Asistencia, Menu, Configuracion

def init_db():
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si ya existe un usuario administrador
        admin = Usuario.query.filter_by(email='admin@example.com').first()
        if not admin:
            # Crear usuario administrador por defecto
            admin = Usuario(
                nombre='Administrador',
                email='admin@example.com',
                rol='admin',
                activo=True
            )
            admin.set_password('admin123')  # Cambiar en producción
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado")
        
        print("Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_db() 