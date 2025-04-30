from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from extensions import db
from models import Menu
from datetime import datetime, date, timedelta

menus_bp = Blueprint('menus', __name__)

@menus_bp.route('/menus')
@login_required
def lista_menus():
    fecha_inicio = request.args.get('fecha_inicio', type=date.fromisoformat)
    fecha_fin = request.args.get('fecha_fin', type=date.fromisoformat)
    
    query = Menu.query
    if fecha_inicio:
        query = query.filter(Menu.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Menu.fecha <= fecha_fin)
    
    menus = query.order_by(Menu.fecha.desc()).all()
    return render_template('menus/lista.html', menus=menus)

@menus_bp.route('/menus/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_menu():
    if request.method == 'POST':
        menu = Menu(
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            comida_principal=request.form['comida_principal'],
            guarnicion=request.form['guarnicion'],
            postre=request.form['postre'],
            calorias=request.form.get('calorias', type=int),
            notas=request.form['notas']
        )
        
        try:
            db.session.add(menu)
            db.session.commit()
            flash('Menú registrado exitosamente', 'success')
            return redirect(url_for('menus.lista_menus'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el menú: {str(e)}', 'error')
    
    return render_template('menus/nuevo.html')

@menus_bp.route('/menus/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_menu(id):
    menu = Menu.query.get_or_404(id)
    
    if request.method == 'POST':
        menu.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
        menu.comida_principal = request.form['comida_principal']
        menu.guarnicion = request.form['guarnicion']
        menu.postre = request.form['postre']
        menu.calorias = request.form.get('calorias', type=int)
        menu.notas = request.form['notas']
        
        try:
            db.session.commit()
            flash('Menú actualizado exitosamente', 'success')
            return redirect(url_for('menus.lista_menus'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el menú: {str(e)}', 'error')
    
    return render_template('menus/editar.html', menu=menu)

@menus_bp.route('/menus/semanal')
@login_required
def menu_semanal():
    fecha_actual = date.today()
    inicio_semana = fecha_actual - timedelta(days=fecha_actual.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    menus = Menu.query.filter(
        Menu.fecha >= inicio_semana,
        Menu.fecha <= fin_semana
    ).order_by(Menu.fecha).all()
    
    return render_template('menus/semanal.html', 
                         menus=menus,
                         inicio_semana=inicio_semana,
                         fin_semana=fin_semana)

@menus_bp.route('/menus/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_menu(id):
    menu = Menu.query.get_or_404(id)
    try:
        db.session.delete(menu)
        db.session.commit()
        flash('Menú eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el menú: {str(e)}', 'error')
    
    return redirect(url_for('menus.lista_menus')) 