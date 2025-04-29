from flask import Blueprint, render_template, request, send_file
from flask_login import login_required
from extensions import db
from models import Estudiante, Asistencia, Menu
from datetime import datetime, date, timedelta
from sqlalchemy import func
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reportes')
@login_required
def dashboard():
    # Estadísticas generales
    total_estudiantes = Estudiante.query.count()
    estudiantes_activos = Estudiante.query.filter_by(estado=True).count()
    
    # Asistencias de hoy
    hoy = date.today()
    asistencias_hoy = Asistencia.query.filter(
        func.date(Asistencia.fecha) == hoy
    ).count()
    
    # Asistencias por tipo de estudiante (última semana)
    fecha_inicio = date.today() - timedelta(days=7)
    asistencias_por_tipo = db.session.query(
        Estudiante.tipo_estudiante,
        func.count(Asistencia.id).label('total')
    ).join(Asistencia).filter(
        func.date(Asistencia.fecha) >= fecha_inicio,
        func.date(Asistencia.fecha) <= hoy
    ).group_by(Estudiante.tipo_estudiante).all()

    # Asegurar que tenemos ambos tipos de estudiantes en los resultados
    tipos_dict = dict(asistencias_por_tipo)
    asistencias_por_tipo = [
        ('becado', tipos_dict.get('becado', 0)),
        ('pagado', tipos_dict.get('pagado', 0))
    ]

    # Asistencias por día (última semana)
    asistencias_semana = db.session.query(
        func.date(Asistencia.fecha).label('fecha'),
        func.count(Asistencia.id).label('total')
    ).filter(
        func.date(Asistencia.fecha) >= fecha_inicio,
        func.date(Asistencia.fecha) <= hoy
    ).group_by(func.date(Asistencia.fecha)).all()

    # Preparar datos para el gráfico con todos los días
    dias = []
    totales = []
    fecha_actual = fecha_inicio
    while fecha_actual <= hoy:
        dias.append(fecha_actual.strftime('%d/%m'))
        total = next(
            (a.total for a in asistencias_semana if a.fecha == fecha_actual),
            0
        )
        totales.append(total)
        fecha_actual += timedelta(days=1)

    # Calcular porcentaje de asistencia diaria de manera segura
    porcentaje_asistencia = round((asistencias_hoy / estudiantes_activos * 100) if estudiantes_activos > 0 else 0)
    
    return render_template('reports/dashboard.html',
                         total_estudiantes=total_estudiantes,
                         estudiantes_activos=estudiantes_activos,
                         asistencias_hoy=asistencias_hoy,
                         asistencias_por_tipo=asistencias_por_tipo,
                         dias=dias,
                         totales=totales,
                         porcentaje_asistencia=porcentaje_asistencia)

@reports_bp.route('/reportes/asistencia')
@login_required
def reporte_asistencia():
    fecha_inicio = request.args.get('fecha_inicio', type=date.fromisoformat)
    fecha_fin = request.args.get('fecha_fin', type=date.fromisoformat)
    tipo_estudiante = request.args.get('tipo_estudiante')
    
    query = db.session.query(
        Estudiante.nombre,
        Estudiante.identificador,
        Estudiante.curso,
        Estudiante.tipo_estudiante,
        db.func.count(Asistencia.id).label('total_asistencias')
    ).join(Asistencia)
    
    if fecha_inicio:
        query = query.filter(Asistencia.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Asistencia.fecha <= fecha_fin)
    if tipo_estudiante:
        query = query.filter(Estudiante.tipo_estudiante == tipo_estudiante)
    
    resultados = query.group_by(
        Estudiante.id,
        Estudiante.nombre,
        Estudiante.identificador,
        Estudiante.curso,
        Estudiante.tipo_estudiante
    ).all()
    
    return render_template('reports/asistencia.html',
                         resultados=resultados,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         tipo_estudiante=tipo_estudiante)

@reports_bp.route('/reportes/exportar/csv')
@login_required
def exportar_csv():
    fecha_inicio = request.args.get('fecha_inicio', type=date.fromisoformat)
    fecha_fin = request.args.get('fecha_fin', type=date.fromisoformat)
    
    query = db.session.query(
        Estudiante.nombre,
        Estudiante.identificador,
        Estudiante.curso,
        Estudiante.tipo_estudiante,
        Asistencia.fecha,
        Asistencia.hora,
        Asistencia.metodo_registro
    ).join(Asistencia)
    
    if fecha_inicio:
        query = query.filter(Asistencia.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Asistencia.fecha <= fecha_fin)
    
    resultados = query.order_by(Asistencia.fecha.desc()).all()
    
    # Crear DataFrame
    df = pd.DataFrame(resultados, columns=[
        'Nombre', 'Identificador', 'Curso', 'Tipo de Estudiante', 'Fecha', 'Hora', 'Método'
    ])
    
    # Exportar a CSV
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'asistencias_{date.today()}.csv'
    )

@reports_bp.route('/reportes/exportar/pdf')
@login_required
def exportar_pdf():
    fecha_inicio = request.args.get('fecha_inicio', type=date.fromisoformat)
    fecha_fin = request.args.get('fecha_fin', type=date.fromisoformat)
    
    # Obtener datos
    query = db.session.query(
        Estudiante.nombre,
        Estudiante.identificador,
        Estudiante.curso,
        Estudiante.tipo_estudiante,
        db.func.count(Asistencia.id).label('total_asistencias')
    ).join(Asistencia)
    
    if fecha_inicio:
        query = query.filter(Asistencia.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Asistencia.fecha <= fecha_fin)
    
    resultados = query.group_by(
        Estudiante.id,
        Estudiante.nombre,
        Estudiante.identificador,
        Estudiante.curso,
        Estudiante.tipo_estudiante
    ).all()
    
    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Reporte de Asistencias", styles['Title']))
    elements.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", styles['Normal']))
    
    # Tabla de datos
    data = [['Nombre', 'Identificador', 'Curso', 'Tipo', 'Total Asistencias']]
    for r in resultados:
        data.append([r.nombre, r.identificador, r.curso, r.tipo_estudiante, str(r.total_asistencias)])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'reporte_asistencias_{date.today()}.pdf'
    ) 