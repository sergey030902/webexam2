from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Book, Genre, Cover, Review
from tools import ImageSaver
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from markdown2 import markdown
from auth import checkRole
import bleach
import os
from configure import UPLOAD_FOLDER
from markupsafe import Markup

bp = Blueprint('book', __name__, url_prefix='/book')

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + ['p', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'blockquote', 'code', 'pre']
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title']
}

@bp.route('/create_book', methods=['GET', 'POST'])
@login_required
@checkRole('create_book')
def create_book():
    genres = db.session.execute(db.select(Genre)).scalars()
    book = Book()
    if request.method == "POST":
        title = request.form.get('name')
        description_md = request.form.get('short_desc')
        year = request.form.get('year')
        publisher = request.form.get('publisher')
        author = request.form.get('author')
        pages = request.form.get('pages')
        file = request.files.get('book_cover')
        genre_ids = request.form.getlist('genres')

        description_html = bleach.clean(markdown(description_md), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        book = Book(
            title=title,
            description=description_html,
            year=year,
            publisher=publisher,
            author=author,
            pages=pages
        )

        book.genres = db.session.query(Genre).filter(Genre.id.in_(genre_ids)).all()

        try:
            if file and file.filename:
                img = ImageSaver(file).save()
                book.cover_id = img.id
            else:
                raise ValueError("Обложка книги обязательна")
            
            db.session.add(book)
            db.session.commit()
            
            flash(f'Книга {book.title} была успешно добавлена!', 'success')
            return redirect(url_for('index'))
        
        except IntegrityError as err:
            flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
            db.session.rollback()
    
    return render_template('books/create_book.html', genres=genres, current_user=current_user, book=book)

@bp.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
@checkRole('edit_book')
def edit_book(book_id):
    book = db.session.query(Book).filter_by(id=book_id).first()
    genres = db.session.execute(db.select(Genre)).scalars()
    
    if request.method == "POST":
        title = request.form.get('name')
        description_md = request.form.get('short_desc')
        year = request.form.get('year')
        publisher = request.form.get('publisher')
        author = request.form.get('author')
        pages = request.form.get('pages')
        genre_ids = request.form.getlist('genres')
        
        book.title = title
        book.description = bleach.clean(markdown(description_md), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        book.publisher = publisher
        book.author = author
        book.pages = pages
        book.year = year

        book.genres = db.session.query(Genre).filter(Genre.id.in_(genre_ids)).all()

        try:
            db.session.add(book)
            db.session.commit()
            flash(f'Книга {book.title} была успешно обновлена!', 'success')
            return redirect(url_for('index'))
        
        except IntegrityError as err:
            flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
            db.session.rollback()
    
    return render_template('books/edit_book.html', book=book, genres=genres, current_user=current_user)

@bp.route('/delete_book/<int:book_id>', methods=["POST"])
@login_required
@checkRole('delete_book')
def delete_book(book_id):
    book = db.session.query(Book).filter_by(id=book_id).first()
    if book is None:
        flash(f'Книга с id {book_id} не найдена.', 'danger')
        return redirect(url_for('index'))

    try:
        cover_id = book.cover_id
        db.session.delete(book)
        db.session.commit()

        # Проверка на наличие других книг с этой обложкой
        cover = db.session.query(Cover).filter_by(id=cover_id).first()
        if cover:
            related_books = db.session.query(Book).filter_by(cover_id=cover.id).count()
            if related_books == 0:
                file_path = os.path.join(UPLOAD_FOLDER, cover.storage_filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(cover)
                db.session.commit()

        flash(f'Книга "{book.title}" была успешно удалена!', 'success')

    except SQLAlchemyError as err:
        flash(f'Возникла ошибка при удалении книги. ({err})', 'danger')
        db.session.rollback()

    return redirect(url_for('index'))

@bp.route('/show_book/<int:book_id>', methods=["GET"])
@login_required
def show_book(book_id):
    book = db.session.query(Book).filter_by(id=book_id).first_or_404()
    cover = db.session.query(Cover).filter_by(id=book.cover_id).first()
    reviews = db.session.query(Review).filter_by(book_id=book_id).all()
    user_review = db.session.query(Review).filter_by(book_id=book_id, user_id=current_user.id).first()

    books_with_genres_cover = {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'publisher': book.publisher,
        'pages': book.pages,
        'description': Markup(book.description),
        'year': book.year,
        'genres': [genre.name for genre in book.genres],
        'cover': cover.url if cover else None,
    }

    return render_template('books/show_book.html', book=books_with_genres_cover, current_user=current_user, user_review=user_review, reviews=reviews)
