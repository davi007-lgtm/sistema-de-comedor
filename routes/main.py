from flask import Blueprint, render_template
from flask_login import login_required
from models import Estudiante, Asistencia, Menu
from datetime import datetime, date, timedelta
from sqlalchemy import func, cast, Date

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    # Fecha actual
    hoy = date.today()
    current_date = datetime.now()  # Para mostrar la fecha completa con nombre del día
    
    # Estadísticas generales
    asistencias_hoy = Asistencia.query.filter(
        cast(Asistencia.fecha, Date) == hoy
    ).count()
    
    total_estudiantes = Estudiante.query.count()
    estudiantes_becados = Estudiante.query.filter_by(tipo_estudiante='becado', estado=True).count()
    estudiantes_pagados = total_estudiantes - estudiantes_becados
    menus_activos = Menu.query.filter(Menu.fecha >= hoy).count()

    # Datos para el gráfico de asistencias (últimos 7 días)
    fecha_inicio = hoy - timedelta(days=6)
    asistencias_semana = Asistencia.query.filter(
        Asistencia.fecha >= fecha_inicio,
        Asistencia.fecha <= hoy
    ).with_entities(
        Asistencia.fecha,
        func.count(Asistencia.id).label('total')
    ).group_by(Asistencia.fecha).all()

    # Preparar datos para el gráfico
    dias = []
    asistencias_por_dia = []
    fecha_actual = fecha_inicio
    
    # Inicializar el diccionario con todas las fechas en 0
    asistencias_dict = {fecha_actual + timedelta(days=i): 0 for i in range(7)}
    
    # Actualizar con las asistencias reales
    for asistencia in asistencias_semana:
        if asistencia.fecha in asistencias_dict:
            asistencias_dict[asistencia.fecha] = asistencia.total

    # Convertir a listas para el gráfico
    for fecha in sorted(asistencias_dict.keys()):
        dias.append(fecha.strftime('%d/%m'))
        asistencias_por_dia.append(asistencias_dict[fecha])

    # Últimas asistencias
    ultimas_asistencias = Asistencia.query.join(Estudiante).order_by(
        Asistencia.fecha.desc(),
        Asistencia.hora.desc()
    ).limit(5).all()

    # Menú del día
    menu_hoy = Menu.query.filter_by(fecha=hoy).first()

    return render_template('main/index.html',
                         current_date=current_date,
                         asistencias_hoy=asistencias_hoy,
                         total_estudiantes=total_estudiantes,
                         estudiantes_becados=estudiantes_becados,
                         estudiantes_pagados=estudiantes_pagados,
                         menus_activos=menus_activos,
                         dias=dias,
                         asistencias_por_dia=asistencias_por_dia,
                         ultimas_asistencias=ultimas_asistencias,
                         menu_hoy=menu_hoy) 