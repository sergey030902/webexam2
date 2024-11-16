from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Book, Genre, Cover, Review, Collection
from tools import ImageSaver
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from markdown2 import markdown
from auth import checkRole
import bleach
import os
from configure import UPLOAD_FOLDER
from markupsafe import Markup

bp = Blueprint('collection', __name__, url_prefix='/collection')

@bp.route('/show_collection/<int:user_id>', methods=["GET"])
@login_required
def show_collection(user_id):
    collections = db.session.query(Collection).filter_by(user_id=user_id).all()
    return render_template('collections/user_collections.html', collections=collections)

@bp.route('/add_collection', methods=['POST'])
@login_required
def add_collection():
    name = request.form.get('name')
    if not name:
        flash('Название подборки не может быть пустым', 'danger')
        return redirect(url_for('index'))

    collection = Collection(name=name, user_id=current_user.id)
    db.session.add(collection)
    db.session.commit()
    flash('Подборка успешно добавлена!', 'success')
    return redirect(url_for('collection.show_collection', user_id=current_user.id))

@bp.route('/current_collection/<int:collection_id>', methods=["GET"])
@login_required
def current_collection(collection_id):
    collection = db.session.query(Collection).filter_by(id=collection_id, user_id=current_user.id).first()
    if not collection:
        flash('Подборка не найдена.', 'danger')
        return redirect(url_for('collection.show_collection', user_id=current_user.id))
    books = collection.books
    return render_template('collections/current_collection.html', collection=collection, books=books)


@bp.route('/add_to_collection', methods=['POST'])
@login_required
def add_to_collection():
    collection_id = request.form.get('collection_id')
    book_id = request.form.get('book_id')

    collection = db.session.query(Collection).filter_by(id=collection_id, user_id=current_user.id).first()
    book = db.session.query(Book).filter_by(id=book_id).first()

    if not collection or not book:
        flash('Подборка или книга не найдены.', 'danger')
        return redirect(url_for('index'))

    collection.books.append(book)
    db.session.commit()

    flash('Книга успешно добавлена в подборку!', 'success')
    return redirect(url_for('index'))



