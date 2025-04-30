from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
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
    grados = ['1°', '2°', '3°', '4°', '5°', '6°']
    return render_template('students/lista_estudiantes.html', estudiantes=estudiantes, grados=grados)

@students_bp.route('/estudiantes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_estudiante():
    if request.method == 'POST':
        try:
            # Validar campos requeridos
            if not request.form.get('nombre'):
                flash('El nombre es requerido', 'error')
                return render_template('students/nuevo.html')
            if not request.form.get('curso'):
                flash('El grado es requerido', 'error')
                return render_template('students/nuevo.html')
            if not request.form.get('tipo_estudiante'):
                flash('El tipo de estudiante es requerido', 'error')
                return render_template('students/nuevo.html')

            # Generar identificador único
            identificador = f"EST{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            estudiante = Estudiante(
                identificador=identificador,
                nombre=request.form['nombre'].strip(),
                curso=request.form['curso'],
                tipo_estudiante=request.form['tipo_estudiante'],
                estado=True
            )
            db.session.add(estudiante)
            db.session.commit()
            flash('Estudiante registrado exitosamente', 'success')
            return redirect(url_for('students.lista_estudiantes'))
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear estudiante: {str(e)}")  # Para debugging
            flash(f'Error al registrar el estudiante: {str(e)}', 'error')
            return render_template('students/nuevo.html')
    
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

@students_bp.route('/estudiantes/<int:student_id>/qr')
@login_required
def generar_qr(student_id):
    estudiante = Estudiante.query.get_or_404(student_id)
    return render_template('students/qr.html', student=estudiante)

@students_bp.route('/api/estudiantes', methods=['POST'])
@login_required
def crear_estudiante():
    try:
        data = request.json
        # Validar que todos los campos requeridos estén presentes
        required_fields = ['nombre', 'curso']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'El campo {field} es requerido',
                    'error': 'missing_field'
                }), 400

        # Generar identificador único
        identificador = f"EST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Si se envía grado, usarlo como curso
        curso = data.get('grado', data.get('curso'))
        
        estudiante = Estudiante(
            identificador=identificador,
            nombre=data['nombre'],
            curso=curso,
            tipo_estudiante=data.get('tipo_estudiante', 'pagado'),  # valor por defecto si no se especifica
            estado=True
        )
        
        db.session.add(estudiante)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'id': estudiante.id,
            'message': 'Estudiante creado exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        # Log del error para debugging
        print(f"Error al crear estudiante: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al crear el estudiante: ' + str(e),
            'error': 'database_error'
        }), 400

@students_bp.route('/api/estudiantes/<int:student_id>', methods=['PUT'])
@login_required
def actualizar_estudiante(student_id):
    try:
        estudiante = Estudiante.query.get_or_404(student_id)
        data = request.json
        
        if 'nombre' in data:
            estudiante.nombre = data['nombre']
        if 'curso' in data:
            estudiante.curso = data['curso']
        if 'tipo_estudiante' in data:
            estudiante.tipo_estudiante = data['tipo_estudiante']
        if 'estado' in data:
            estudiante.estado = data['estado']
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Estudiante actualizado exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al actualizar el estudiante',
            'error': str(e)
        }), 400

@students_bp.route('/api/estudiantes/<int:student_id>/toggle', methods=['POST'])
@login_required
def toggle_status(student_id):
    try:
        estudiante = Estudiante.query.get_or_404(student_id)
        estudiante.estado = not estudiante.estado
        db.session.commit()
        return jsonify({
            'success': True,
            'activo': estudiante.estado,
            'message': f'Estado del estudiante {"activado" if estudiante.estado else "desactivado"} exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al cambiar el estado del estudiante',
            'error': str(e)
        }), 400 