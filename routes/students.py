from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Estudiante
from datetime import datetime
import qrcode
from io import BytesIO
import base64

students_bp = Blueprint('students', __name__)

@students_bp.route('/estudiantes')
@login_required
def lista_estudiantes():
    estudiantes = Estudiante.query.all()
    return render_template('students/lista.html', estudiantes=estudiantes)

@students_bp.route('/estudiantes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_estudiante():
    if request.method == 'POST':
        # Generar identificador único (puede ser un número secuencial o un UUID)
        identificador = f"EST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        estudiante = Estudiante(
            identificador=identificador,
            nombre=request.form['nombre'],
            curso=request.form['curso'],
            tipo_estudiante=request.form['tipo_estudiante'],
            estado=True
        )
        db.session.add(estudiante)
        try:
            db.session.commit()
            flash('Estudiante registrado exitosamente', 'success')
            return redirect(url_for('students.lista_estudiantes'))
        except:
            db.session.rollback()
            flash('Error al registrar el estudiante', 'error')
    
    return render_template('students/nuevo.html')

@students_bp.route('/estudiantes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_estudiante(id):
    estudiante = Estudiante.query.get_or_404(id)
    
    if request.method == 'POST':
        estudiante.nombre = request.form['nombre']
        estudiante.curso = request.form['curso']
        estudiante.tipo_estudiante = request.form['tipo_estudiante']
        estudiante.estado = request.form.get('estado', type=bool)
        
        try:
            db.session.commit()
            flash('Estudiante actualizado exitosamente', 'success')
            return redirect(url_for('students.lista_estudiantes'))
        except:
            db.session.rollback()
            flash('Error al actualizar el estudiante', 'error')
    
    return render_template('students/editar.html', estudiante=estudiante)

@students_bp.route('/estudiantes/<int:id>/historial')
@login_required
def historial_estudiante(id):
    estudiante = Estudiante.query.get_or_404(id)
    return render_template('students/historial.html', estudiante=estudiante)

@students_bp.route('/estudiantes/<int:id>/toggle-estado')
@login_required
def toggle_estado(id):
    estudiante = Estudiante.query.get_or_404(id)
    estudiante.estado = not estudiante.estado
    try:
        db.session.commit()
        estado = "activado" if estudiante.estado else "desactivado"
        flash(f'Acceso al comedor {estado} exitosamente', 'success')
    except:
        db.session.rollback()
        flash('Error al cambiar el estado del estudiante', 'error')
    
    return redirect(url_for('students.lista_estudiantes'))

@students_bp.route('/estudiantes/<int:id>/qr')
@login_required
def generar_qr(id):
    estudiante = Estudiante.query.get_or_404(id)
    
    # Generar QR con el identificador del estudiante
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(estudiante.identificador)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('students/qr.html', 
                         estudiante=estudiante, 
                         qr_code=qr_base64) 