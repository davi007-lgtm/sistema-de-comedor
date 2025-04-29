from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Estudiante, Asistencia
from datetime import datetime, date, time
from sqlalchemy import func, case
import qrcode
from io import BytesIO
import base64

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/asistencia')
@login_required
def index():
    return redirect(url_for('attendance.registrar_asistencia'))

@attendance_bp.route('/asistencia/registrar', methods=['GET', 'POST'])
@login_required
def registrar_asistencia():
    if request.method == 'GET':
        # Obtener las últimas asistencias registradas
        ultimas_asistencias = Asistencia.query.join(Estudiante).order_by(
            Asistencia.fecha.desc(),
            Asistencia.hora.desc()
        ).limit(10).all()
        
        return render_template('attendance/registrar.html',
                            estudiantes=[],
                            ultimas_asistencias=ultimas_asistencias)

    # Procesar el registro de asistencia (POST)
    identificador = request.form.get('cedula')  # Mantenemos 'cedula' en el form por compatibilidad
    observaciones = request.form.get('observaciones', '').strip()
    
    if not identificador:
        flash('El identificador del estudiante es requerido', 'error')
        return redirect(url_for('attendance.registrar_asistencia'))
    
    try:
        # Buscar estudiante
        estudiante = Estudiante.query.filter_by(identificador=identificador).first()
        
        if not estudiante:
            flash('Estudiante no encontrado', 'error')
            return redirect(url_for('attendance.registrar_asistencia'))
        
        if not estudiante.estado:
            flash('El estudiante está inactivo', 'error')
            return redirect(url_for('attendance.registrar_asistencia'))
        
        # Verificar asistencia existente
        hoy = date.today()
        asistencia_existente = Asistencia.query.filter_by(
            estudiante_id=estudiante.id,
            fecha=hoy
        ).first()
        
        if asistencia_existente:
            flash('Ya se registró asistencia hoy para este estudiante', 'warning')
            return redirect(url_for('attendance.registrar_asistencia'))
        
        # Registrar nueva asistencia
        asistencia = Asistencia(
            estudiante_id=estudiante.id,
            fecha=hoy,
            hora=datetime.now().time(),
            metodo_registro='manual',
            registrado_por=current_user.id,
            observaciones=observaciones if observaciones else None
        )
        
        db.session.add(asistencia)
        db.session.commit()
        
        flash(f'Asistencia registrada exitosamente para {estudiante.nombre}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error al registrar la asistencia: ' + str(e), 'error')
    
    return redirect(url_for('attendance.registrar_asistencia'))

@attendance_bp.route('/asistencia/buscar', methods=['POST'])
@login_required
def buscar_estudiantes():
    search_type = request.form.get('searchType')
    search_value = request.form.get('searchValue', '').strip()
    
    if not search_type or not search_value:
        return jsonify({
            'error': 'Tipo y valor de búsqueda son requeridos',
            'estudiantes': []
        }), 400
    
    try:
        query = Estudiante.query
        
        if search_type == 'cedula':
            query = query.filter(Estudiante.identificador.ilike(f'%{search_value}%'))
        elif search_type == 'nombre':
            query = query.filter(Estudiante.nombre.ilike(f'%{search_value}%'))
        elif search_type == 'curso':
            query = query.filter(Estudiante.curso.ilike(f'%{search_value}%'))
        else:
            return jsonify({
                'error': 'Tipo de búsqueda no válido',
                'estudiantes': []
            }), 400
        
        estudiantes = query.filter_by(estado=True).all()
        
        return jsonify({
            'estudiantes': [{
                'cedula': e.identificador,  # Mantenemos 'cedula' en la respuesta por compatibilidad
                'nombre': e.nombre,
                'curso': e.curso,
                'becado': e.tipo_estudiante == 'becado'
            } for e in estudiantes]
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error en la búsqueda: {str(e)}',
            'estudiantes': []
        }), 500

@attendance_bp.route('/asistencia/historial')
@login_required
def historial():
    fecha_inicio = request.args.get('fecha_inicio', type=str)
    fecha_fin = request.args.get('fecha_fin', type=str)
    
    query = Asistencia.query
    
    if fecha_inicio:
        query = query.filter(Asistencia.fecha >= datetime.strptime(fecha_inicio, '%Y-%m-%d').date())
    if fecha_fin:
        query = query.filter(Asistencia.fecha <= datetime.strptime(fecha_fin, '%Y-%m-%d').date())
    
    asistencias = query.order_by(Asistencia.fecha.desc(), Asistencia.hora.desc()).all()
    return render_template('attendance/historial.html', asistencias=asistencias)

@attendance_bp.route('/estudiantes/<int:id>/qr')
@login_required
def generar_qr(id):
    estudiante = Estudiante.query.get_or_404(id)
    
    # Generar QR con la matrícula del estudiante
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(estudiante.matricula)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('attendance/qr.html', 
                         estudiante=estudiante, 
                         qr_code=qr_base64)

@attendance_bp.route('/resumen')
def resumen():
    # Obtener el mes y año actual si no se especifican
    mes = request.args.get('mes', datetime.now().month)
    anio = request.args.get('anio', datetime.now().year)
    
    try:
        mes = int(mes)
        anio = int(anio)
    except ValueError:
        mes = datetime.now().month
        anio = datetime.now().year

    # Obtener estadísticas generales
    total_asistencias = Asistencia.query.filter(
        func.extract('month', Asistencia.hora) == mes,
        func.extract('year', Asistencia.hora) == anio
    ).count()

    # Obtener asistencias por tipo de estudiante
    asistencias_becados = db.session.query(func.count(Asistencia.id)).join(Estudiante).filter(
        Estudiante.tipo_estudiante == 'becado',
        func.extract('month', Asistencia.hora) == mes,
        func.extract('year', Asistencia.hora) == anio
    ).scalar()

    asistencias_pagados = total_asistencias - (asistencias_becados or 0)

    # Obtener asistencias por día
    asistencias_por_dia = db.session.query(
        func.date(Asistencia.hora).label('fecha'),
        func.count(Asistencia.id).label('total')
    ).filter(
        func.extract('month', Asistencia.hora) == mes,
        func.extract('year', Asistencia.hora) == anio
    ).group_by(func.date(Asistencia.hora)).all()

    # Obtener asistencias por curso
    asistencias_por_curso = db.session.query(
        Estudiante.curso,
        func.count(Asistencia.id).label('total'),
        func.sum(case([(Estudiante.tipo_estudiante == 'becado', 1)], else_=0)).label('becados'),
        func.sum(case([(Estudiante.tipo_estudiante == 'pagado', 1)], else_=0)).label('pagados')
    ).join(Estudiante).filter(
        func.extract('month', Asistencia.hora) == mes,
        func.extract('year', Asistencia.hora) == anio
    ).group_by(Estudiante.curso).all()

    return render_template('attendance/resumen.html',
                         mes=mes,
                         anio=anio,
                         total_asistencias=total_asistencias,
                         asistencias_becados=asistencias_becados,
                         asistencias_pagados=asistencias_pagados,
                         asistencias_por_dia=asistencias_por_dia,
                         asistencias_por_curso=asistencias_por_curso) 