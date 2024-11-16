from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required,current_user
from models import db, User
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

bp = Blueprint('auth', __name__, url_prefix='/auth')

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Для доступа к данной странице необходимо пройти процедуру аутентификации.'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)
    login_manager.init_app(app)

def load_user(user_id):
    user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar()
    return user

def checkRole(action):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if current_user.can(action):
                return f(*args, **kwargs)
            flash("У вас нет доступа к этой странице", "danger")
            return redirect(url_for('index'))
        return wrapper
    return decorator

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('login')
        password = request.form.get('password')
        if username and password:
            user = db.session.query(User).filter_by(username=username).first()
            if user:
                if check_password_hash(user.password_hash, password):
                    login_user(user)
                    flash('Вы успешно аутентифицированы.', 'success')
                    next = request.args.get('next')
                    return redirect(next or url_for('index'))
                else:
                    flash('Неверный пароль.', 'danger')
            else:
                flash('Пользователь не найден.', 'danger')
        else:
            flash('Пожалуйста, введите логин и пароль.', 'danger')
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))