from app import db
from datetime import datetime
import os
from PIL import Image
from werkzeug.utils import secure_filename

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # image, document, video, etc.
    mime_type = db.Column(db.String(100))
    size = db.Column(db.Integer)  # in bytes
    dimensions = db.Column(db.String(50))  # for images: WxH
    alt_text = db.Column(db.String(255))
    caption = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    folder = db.Column(db.String(255), default='')  # Virtual folder path
    is_public = db.Column(db.Boolean, default=True)
    
    @property
    def url(self):
        return f'/uploads/{self.file_path}'
    
    @property
    def thumbnail_url(self):
        if self.file_type != 'image':
            return None
        name, ext = os.path.splitext(self.file_path)
        return f'/uploads/thumbnails/{name}_thumb{ext}'
    
    @property
    def preview_url(self):
        if self.file_type == 'image':
            return self.url
        elif self.file_type == 'document':
            return '/static/img/document-icon.png'
        elif self.file_type == 'video':
            return '/static/img/video-icon.png'
        return '/static/img/file-icon.png'
    
    def generate_thumbnail(self, upload_path):
        """Generate thumbnail for image files"""
        if self.file_type != 'image':
            return
            
        img = Image.open(os.path.join(upload_path, self.file_path))
        
        # Calculate thumbnail size maintaining aspect ratio
        max_size = (300, 300)
        ratio = min(max_size[0]/img.size[0], max_size[1]/img.size[1])
        thumb_size = tuple([int(x*ratio) for x in img.size])
        
        # Create thumbnail
        img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        
        # Save thumbnail
        name, ext = os.path.splitext(self.file_path)
        thumb_path = os.path.join(upload_path, 'thumbnails', f'{name}_thumb{ext}')
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        img.save(thumb_path, quality=85, optimize=True)

class MediaFolder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False, unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('media_folder.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __str__(self):
        return self.path
