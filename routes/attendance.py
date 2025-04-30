from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Estudiante, Asistencia
from datetime import datetime, date, time, timedelta
from sqlalchemy import func, case
import qrcode
from io import BytesIO
import base64

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/asistencia')
@login_required
def index():
    """Página principal de asistencias"""
    ultimas_asistencias = Asistencia.query.join(Estudiante).order_by(
        Asistencia.fecha.desc()
    ).limit(10).all()
    
    return render_template('attendance/registrar.html',
                         ultimas_asistencias=ultimas_asistencias)

@attendance_bp.route('/asistencia/scanner')
@login_required
def scanner():
    """Vista para el escáner de códigos QR"""
    return render_template('attendance/scanner.html')

@attendance_bp.route('/asistencia/manual')
@login_required
def registro_manual():
    """Vista para el registro manual de asistencias"""
    ultimas_asistencias = Asistencia.query.join(Estudiante).order_by(
        Asistencia.fecha.desc()
    ).limit(10).all()
    
    return render_template('attendance/registrar.html',
                         ultimas_asistencias=ultimas_asistencias)

@attendance_bp.route('/asistencia/historial')
@login_required
def historial():
    """Vista para el historial de asistencias"""
    fecha_inicio = request.args.get('fecha_inicio', type=str)
    fecha_fin = request.args.get('fecha_fin', type=str)
    
    query = Asistencia.query.join(Estudiante)
    
    if fecha_inicio:
        query = query.filter(Asistencia.fecha >= datetime.strptime(fecha_inicio, '%Y-%m-%d').date())
    if fecha_fin:
        query = query.filter(Asistencia.fecha <= datetime.strptime(fecha_fin, '%Y-%m-%d').date())
    
    asistencias = query.order_by(Asistencia.fecha.desc()).all()
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

@attendance_bp.route('/api/asistencias/registrar', methods=['POST'])
@login_required
def api_registrar_asistencia():
    """API endpoint para registrar asistencia"""
    try:
        data = request.json
        estudiante_id = data['estudiante_id']
        tipo = data['tipo']

        # Verificar si el estudiante existe
        estudiante = Estudiante.query.get_or_404(estudiante_id)
        
        # Verificar si el estudiante está activo
        if not estudiante.estado:
            return jsonify({
                'success': False,
                'message': 'El estudiante no está activo'
            }), 400

        # Verificar si ya existe un registro para este tipo de comida hoy
        hoy = datetime.utcnow().date()
        registro_existente = Asistencia.query.filter(
            Asistencia.estudiante_id == estudiante_id,
            Asistencia.tipo == tipo,
            db.func.date(Asistencia.fecha) == hoy
        ).first()

        if registro_existente:
            return jsonify({
                'success': False,
                'message': f'Ya existe un registro de {tipo} para este estudiante hoy'
            }), 400

        # Crear nuevo registro de asistencia
        asistencia = Asistencia(
            estudiante_id=estudiante_id,
            tipo=tipo,
            registrado_por=current_user.id
        )
        db.session.add(asistencia)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Asistencia registrada exitosamente',
            'estudiante_nombre': estudiante.nombre,
            'tipo': tipo,
            'fecha': asistencia.fecha.isoformat()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error al registrar la asistencia',
            'error': str(e)
        }), 400

@attendance_bp.route('/api/asistencias/buscar', methods=['POST'])
@login_required
def api_buscar_estudiante():
    """API endpoint para buscar estudiantes"""
    try:
        data = request.json
        valor = data.get('valor', '').strip()
        tipo = data.get('tipo', 'identificador')

        if not valor:
            return jsonify({
                'success': False,
                'message': 'El valor de búsqueda es requerido'
            }), 400

        query = Estudiante.query

        if tipo == 'identificador':
            query = query.filter(Estudiante.identificador.ilike(f'%{valor}%'))
        elif tipo == 'nombre':
            query = query.filter(Estudiante.nombre.ilike(f'%{valor}%'))
        elif tipo == 'grado':
            query = query.filter(Estudiante.grado.ilike(f'%{valor}%'))
        else:
            return jsonify({
                'success': False,
                'message': 'Tipo de búsqueda no válido'
            }), 400

        estudiantes = query.filter_by(estado=True).all()
        return jsonify({
            'success': True,
            'estudiantes': [estudiante.to_dict() for estudiante in estudiantes]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error en la búsqueda',
            'error': str(e)
        }), 400

@attendance_bp.route('/api/asistencias/historial', methods=['GET'])
@login_required
def api_obtener_historial():
    """API endpoint para obtener historial de asistencias"""
    try:
        fecha_inicio = request.args.get('fecha_inicio', default=datetime.utcnow().date().isoformat())
        fecha_fin = request.args.get('fecha_fin', default=datetime.utcnow().date().isoformat())
        
        asistencias = Asistencia.query.filter(
            db.func.date(Asistencia.fecha).between(fecha_inicio, fecha_fin)
        ).order_by(Asistencia.fecha.desc()).all()

        return jsonify({
            'success': True,
            'asistencias': [asistencia.to_dict() for asistencia in asistencias]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al obtener el historial',
            'error': str(e)
        }), 400

@attendance_bp.route('/asistencia/registrar', methods=['POST'])
@login_required
def registrar_asistencia():
    """Ruta para registrar asistencia manualmente"""
    try:
        identificador = request.form['identificador']
        tipo = request.form.get('tipo', 'almuerzo')
        observaciones = request.form.get('observaciones', '')

        # Buscar estudiante por identificador
        estudiante = Estudiante.query.filter_by(identificador=identificador).first()
        if not estudiante:
            flash('Estudiante no encontrado', 'error')
            return redirect(url_for('attendance.registro_manual'))

        # Verificar si el estudiante está activo
        if not estudiante.estado:
            flash('El estudiante no está activo', 'error')
            return redirect(url_for('attendance.registro_manual'))

        # Verificar si ya existe un registro para este tipo de comida hoy
        hoy = datetime.utcnow().date()
        registro_existente = Asistencia.query.filter(
            Asistencia.estudiante_id == estudiante.id,
            Asistencia.tipo == tipo,
            db.func.date(Asistencia.fecha) == hoy
        ).first()

        if registro_existente:
            flash(f'Ya existe un registro de {tipo} para este estudiante hoy', 'warning')
            return redirect(url_for('attendance.registro_manual'))

        # Crear nuevo registro de asistencia
        asistencia = Asistencia(
            estudiante_id=estudiante.id,
            tipo=tipo,
            metodo_registro='manual',
            registrado_por=current_user.id,
            observaciones=observaciones
        )
        db.session.add(asistencia)
        db.session.commit()

        flash(f'Asistencia registrada exitosamente para {estudiante.nombre}', 'success')
        return redirect(url_for('attendance.registro_manual'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar la asistencia: {str(e)}', 'error')
        return redirect(url_for('attendance.registro_manual')) 