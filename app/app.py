from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from models import db, Cover, Book, Collection
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask_migrate import Migrate
from auth import bp as auth_bp, init_login_manager
from tools import ImageSaver
import os

app = Flask(__name__)
# application = app

app.config.from_pyfile('configure.py')

db.init_app(app)
migrate = Migrate(app, db)

init_login_manager(app)

from auth import bp as bp_auth
from books_func import bp as bp_books
from review import bp as bp_review
from collection import bp as bp_collection

app.register_blueprint(bp_auth)
app.register_blueprint(bp_books)
app.register_blueprint(bp_review)
app.register_blueprint(bp_collection)

@app.errorhandler(SQLAlchemyError)
def handle_sqlalchemy_error(err):
    error_msg = ('Возникла ошибка при подключении к базе данных. '
                 'Повторите попытку позже.')
    return f'{error_msg} (Подробнее: {err})', 500

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    books = db.session.query(Book).order_by(Book.year.desc()).paginate(page=page, per_page=per_page)
    user_collections = db.session.query(Collection).filter_by(user_id=current_user.id).all() if current_user.is_authenticated else []
    books_with_details = []
    for book in books.items:
        genres = [genre.name for genre in book.genres]
        books_with_details.append({
            'id': book.id,
            'title': book.title,
            'year': book.year,
            'genres': genres,
            'average_rating': book.average_rating,
            'reviews_count': book.reviews_count
        })
    return render_template('index.html', books=books_with_details, books_pog=books, user_collections=user_collections)

@app.route('/images/<image_id>')
def image(image_id):
    img = db.get_or_404(Cover, image_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], img.storage_filename)


