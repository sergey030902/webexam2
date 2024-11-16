import os
import hashlib
from models import db, Cover
from flask import current_app

class ImageSaver:
    def __init__(self, file):
        self.file = file

    def save(self):
        filename = self.file.filename
        mime_type = self.file.mimetype
        file_data = self.file.read()
        
        # Вычисляем MD5-хэш файла
        md5_hash = hashlib.md5(file_data).hexdigest()
        
        # Проверяем, существует ли изображение с таким же хэшем
        existing_cover = db.session.query(Cover).filter_by(md5_hash=md5_hash).first()
        if existing_cover:
            return existing_cover
        
        # Если изображение не найдено, сохраняем новый файл
        ext = os.path.splitext(filename)[1]
        storage_filename = f"{md5_hash}{ext}"
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, storage_filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        cover = Cover(filename=filename, mime_type=mime_type, md5_hash=md5_hash)
        db.session.add(cover)
        db.session.commit()
        
        return cover
