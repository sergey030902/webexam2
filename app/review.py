from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import bleach
from markdown2 import markdown
from models import db, Review
from datetime import datetime, timezone

bp = Blueprint('review', __name__, url_prefix='/review')

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'blockquote', 'code', 'pre'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title']
}

@bp.route('/make_review/<int:book_id>', methods=['GET', 'POST'])
@login_required
def make_review(book_id):

    if request.method == "POST":
        review = request.form.get('review')
        description_md = request.form.get('text')

        description_html = bleach.clean(markdown(description_md), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        review_table = Review(
            book_id=book_id,
            user_id=current_user.id,  # Получаем ID текущего пользователя
            rating=review,
            text=description_html
        )
        try:
            db.session.add(review_table)
            db.session.commit()
            
            flash('Оценка была успешно добавлена!', 'success')
            return redirect(url_for('book.show_book', book_id=book_id))
        
        except IntegrityError as err:
            flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
            db.session.rollback()

    return render_template('review/make_review.html')
