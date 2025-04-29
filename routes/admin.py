from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Usuario, Configuracion
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('Acceso denegado. Se requieren privilegios de administrador.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def dashboard():
    total_usuarios = Usuario.query.count()
    usuarios_activos = Usuario.query.filter_by(activo=True).count()
    return render_template('admin/dashboard.html',
                         total_usuarios=total_usuarios,
                         usuarios_activos=usuarios_activos)

@admin_bp.route('/admin/usuarios')
@login_required
@admin_required
def lista_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios/lista.html', usuarios=usuarios)

@admin_bp.route('/admin/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_usuario():
    if request.method == 'POST':
        usuario = Usuario(
            nombre=request.form['nombre'],
            email=request.form['email'],
            rol=request.form['rol'],
            activo=True
        )
        usuario.set_password(request.form['password'])
        
        try:
            db.session.add(usuario)
            db.session.commit()
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('admin.lista_usuarios'))
        except:
            db.session.rollback()
            flash('Error al crear el usuario', 'error')
    
    return render_template('admin/usuarios/nuevo.html')

@admin_bp.route('/admin/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.email = request.form['email']
        usuario.rol = request.form['rol']
        usuario.activo = request.form.get('activo', type=bool)
        
        if request.form.get('password'):
            usuario.set_password(request.form['password'])
        
        try:
            db.session.commit()
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('admin.lista_usuarios'))
        except:
            db.session.rollback()
            flash('Error al actualizar el usuario', 'error')
    
    return render_template('admin/usuarios/editar.html', usuario=usuario)

@admin_bp.route('/admin/configuracion', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracion():
    if request.method == 'POST':
        # Actualizar configuraciones
        for key, value in request.form.items():
            if key.startswith('config_'):
                config_key = key.replace('config_', '')
                config = Configuracion.query.filter_by(clave=config_key).first()
                if config:
                    config.valor = value
                else:
                    config = Configuracion(clave=config_key, valor=value)
                    db.session.add(config)
        
        try:
            db.session.commit()
            flash('Configuración actualizada exitosamente', 'success')
        except:
            db.session.rollback()
            flash('Error al actualizar la configuración', 'error')
    
    configuraciones = Configuracion.query.all()
    return render_template('admin/configuracion.html', 
                         configuraciones=configuraciones)

@admin_bp.route('/admin/horarios', methods=['GET', 'POST'])
@login_required
@admin_required
def horarios():
    if request.method == 'POST':
        # Actualizar horarios
        horarios = {
            'hora_inicio': request.form['hora_inicio'],
            'hora_fin': request.form['hora_fin'],
            'dias_servicio': request.form['dias_servicio']
        }
        
        for key, value in horarios.items():
            config = Configuracion.query.filter_by(clave=key).first()
            if config:
                config.valor = value
            else:
                config = Configuracion(clave=key, valor=value)
                db.session.add(config)
        
        try:
            db.session.commit()
            flash('Horarios actualizados exitosamente', 'success')
        except:
            db.session.rollback()
            flash('Error al actualizar los horarios', 'error')
    
    configuraciones = Configuracion.query.filter(
        Configuracion.clave.in_(['hora_inicio', 'hora_fin', 'dias_servicio'])
    ).all()
    
    return render_template('admin/horarios.html', 
                         configuraciones=configuraciones) 