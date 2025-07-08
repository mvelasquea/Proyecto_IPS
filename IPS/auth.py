from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
import re

from models import User, db

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validar fortaleza de contraseña"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r'[A-Za-z]', password):
        return False, "La contraseña debe contener al menos una letra"
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe contener al menos un número"
    return True, "Contraseña válida"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registrar nuevo usuario"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['email', 'password', 'nombre', 'apellido']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} es requerido'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        nombre = data['nombre'].strip()
        apellido = data['apellido'].strip()
        cargo = data.get('cargo', '').strip()
        dependencia = data.get('dependencia', '').strip()
        
        # Validar email
        if not validate_email(email):
            return jsonify({'error': 'Formato de email inválido'}), 400
        
        # Validar contraseña
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Crear nuevo usuario
        user = User(
            email=email,
            nombre=nombre,
            apellido=apellido,
            cargo=cargo,
            dependencia=dependencia
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuario registrado exitosamente',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Iniciar sesión"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400
        
        # Buscar usuario
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Email o contraseña incorrectos'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Cuenta desactivada'}), 401
        
        # Iniciar sesión
        login_user(user, remember=True)
        user.update_last_login()
        
        return jsonify({
            'success': True,
            'message': 'Inicio de sesión exitoso',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Cerrar sesión"""
    try:
        logout_user()
        return jsonify({'success': True, 'message': 'Sesión cerrada'})
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Obtener información del usuario actual"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """Verificar si el usuario está autenticado"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    return jsonify({'authenticated': False})