from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, Integer, Table, Column, MetaData, TIMESTAMP
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from check_rights import CheckRights
from flask import url_for
import os
from configure import ADMIN_ROLE_ID, MODERATOR_ROLE_ID, USER_ROLE_ID
from werkzeug.security import generate_password_hash, check_password_hash

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

db = SQLAlchemy(model_class=Base)

class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)

from werkzeug.security import generate_password_hash, check_password_hash

class User(Base, UserMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'), nullable=False)

    role = relationship("Role")
    reviews = relationship("Review", back_populates="user", cascade="all, delete, delete-orphan")
    collections = relationship("Collection", back_populates="user", cascade="all, delete, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return ' '.join([self.last_name, self.first_name, self.middle_name or ''])

    def __repr__(self):
        return '<User %r>' % self.username
    
    def is_admin(self):
        return ADMIN_ROLE_ID == self.role_id
    
    def is_moderator(self):
        return MODERATOR_ROLE_ID == self.role_id
    
    def is_user(self):
        return USER_ROLE_ID == self.role_id
    
    def can(self, action, record=None):
        check_rights = CheckRights(record)
        method = getattr(check_rights, action, None)
        if method:
            return method()
        return False

class Genre(Base):
    __tablename__ = 'genres'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

class Cover(Base):
    __tablename__ = 'covers'

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    md5_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    books = relationship("Book", back_populates="cover")

    def __repr__(self):
        return '<Image %r>' % self.filename

    @property
    def storage_filename(self):
        _, ext = os.path.splitext(self.filename)
        return f"{self.md5_hash}{ext}"

    @property
    def url(self):
        return url_for('image', image_id=self.id, _external=True)

book_genre_table = Table('book_genre', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id'), primary_key=True)
)

class Book(Base):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    publisher: Mapped[str] = mapped_column(String(100), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False)
    cover_id: Mapped[int] = mapped_column(Integer, ForeignKey('covers.id'), nullable=False)

    cover = relationship("Cover", back_populates="books", single_parent=True)
    genres = relationship("Genre", secondary=book_genre_table, back_populates="books")
    reviews = relationship("Review", back_populates="book", cascade="all, delete, delete-orphan")
    collections = relationship("Collection", secondary='collection_book', back_populates="books", cascade="all")

    @property
    def average_rating(self):
        if self.reviews:
            return round(sum(review.rating for review in self.reviews) / len(self.reviews), 2)
        return None

    @property
    def reviews_count(self):
        return len(self.reviews)

Genre.books = relationship("Book", secondary=book_genre_table, back_populates="genres")

class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class Collection(Base):
    __tablename__ = 'collections'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    user = relationship("User", back_populates="collections")
    books = relationship("Book", secondary='collection_book', back_populates="collections", cascade="all, delete")

collection_book_table = Table('collection_book', Base.metadata,
    Column('collection_id', Integer, ForeignKey('collections.id', ondelete="CASCADE"), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id', ondelete="CASCADE"), primary_key=True)
)
