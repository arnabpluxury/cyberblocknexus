from flask import Blueprint, render_template, request, jsonify, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.media import Media, MediaFolder
from app import db
import os
import magic
import mimetypes
from PIL import Image
from datetime import datetime
import hashlib
import json

media = Blueprint('media', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'txt', 'md', 'ppt', 'pptx', 'xls', 'xlsx'},
    'video': {'mp4', 'webm', 'ogg'},
    'other': {'zip', 'rar', '7z'}
}

def allowed_file(filename, file_type=None):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if file_type:
        return ext in ALLOWED_EXTENSIONS.get(file_type, set())
    return ext in {ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts}

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return 'other'

@media.route('/admin/media')
@login_required
def media_library():
    page = request.args.get('page', 1, type=int)
    per_page = 24
    folder = request.args.get('folder', '')
    file_type = request.args.get('type')
    search = request.args.get('search')
    
    query = Media.query
    
    if folder:
        query = query.filter_by(folder=folder)
    if file_type:
        query = query.filter_by(file_type=file_type)
    if search:
        query = query.filter(Media.original_filename.ilike(f'%{search}%'))
    
    files = query.order_by(Media.created_at.desc()).paginate(page=page, per_page=per_page)
    folders = MediaFolder.query.filter_by(parent_id=None).all()
    
    return render_template('admin/media/library.html', 
                         files=files,
                         folders=folders,
                         current_folder=folder)

@media.route('/admin/media/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower()
    hash_name = hashlib.md5(f"{original_filename}{datetime.now()}".encode()).hexdigest()
    filename = f"{hash_name}.{ext}"
    
    # Get folder path
    folder = request.form.get('folder', '')
    relative_path = os.path.join(folder, filename)
    absolute_path = os.path.join(UPLOAD_FOLDER, relative_path)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
    
    # Save file
    file.save(absolute_path)
    
    # Get file info
    file_type = get_file_type(filename)
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(absolute_path)
    size = os.path.getsize(absolute_path)
    dimensions = None
    
    # Handle image specific operations
    if file_type == 'image':
        with Image.open(absolute_path) as img:
            dimensions = f"{img.width}x{img.height}"
    
    # Create media record
    media = Media(
        filename=filename,
        original_filename=original_filename,
        file_path=relative_path,
        file_type=file_type,
        mime_type=mime_type,
        size=size,
        dimensions=dimensions,
        uploaded_by=current_user.id,
        folder=folder,
        alt_text=request.form.get('alt_text', ''),
        caption=request.form.get('caption', '')
    )
    
    db.session.add(media)
    db.session.commit()
    
    # Generate thumbnail for images
    if file_type == 'image':
        media.generate_thumbnail(UPLOAD_FOLDER)
    
    return jsonify({
        'id': media.id,
        'url': media.url,
        'thumbnail_url': media.thumbnail_url,
        'preview_url': media.preview_url,
        'filename': media.original_filename,
        'file_type': media.file_type,
        'size': media.size,
        'dimensions': media.dimensions
    })

@media.route('/admin/media/folder/create', methods=['POST'])
@login_required
def create_folder():
    name = request.form.get('name')
    parent_id = request.form.get('parent_id')
    
    if not name:
        return jsonify({'error': 'Folder name is required'}), 400
    
    # Create folder path
    if parent_id:
        parent = MediaFolder.query.get_or_404(parent_id)
        path = os.path.join(parent.path, secure_filename(name))
    else:
        path = secure_filename(name)
    
    # Check if folder exists
    if MediaFolder.query.filter_by(path=path).first():
        return jsonify({'error': 'Folder already exists'}), 400
    
    folder = MediaFolder(
        name=name,
        path=path,
        parent_id=parent_id,
        created_by=current_user.id
    )
    
    db.session.add(folder)
    db.session.commit()
    
    # Create physical folder
    os.makedirs(os.path.join(UPLOAD_FOLDER, path), exist_ok=True)
    
    return jsonify({
        'id': folder.id,
        'name': folder.name,
        'path': folder.path
    })

@media.route('/admin/media/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_media(id):
    media_item = Media.query.get_or_404(id)
    
    if request.method == 'GET':
        return jsonify({
            'id': media_item.id,
            'filename': media_item.original_filename,
            'url': media_item.url,
            'thumbnail_url': media_item.thumbnail_url,
            'preview_url': media_item.preview_url,
            'file_type': media_item.file_type,
            'size': media_item.size,
            'dimensions': media_item.dimensions,
            'alt_text': media_item.alt_text,
            'caption': media_item.caption,
            'is_public': media_item.is_public
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        media_item.alt_text = data.get('alt_text', media_item.alt_text)
        media_item.caption = data.get('caption', media_item.caption)
        media_item.is_public = data.get('is_public', media_item.is_public)
        db.session.commit()
        return jsonify({'status': 'success'})
    
    elif request.method == 'DELETE':
        # Delete physical files
        file_path = os.path.join(UPLOAD_FOLDER, media_item.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete thumbnail if exists
        if media_item.thumbnail_url:
            thumb_path = os.path.join(UPLOAD_FOLDER, 'thumbnails', 
                                    f"{os.path.splitext(media_item.file_path)[0]}_thumb{os.path.splitext(media_item.file_path)[1]}")
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        
        db.session.delete(media_item)
        db.session.commit()
        return jsonify({'status': 'success'})

@media.route('/admin/media/folder/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_folder(id):
    folder = MediaFolder.query.get_or_404(id)
    
    if request.method == 'GET':
        subfolders = MediaFolder.query.filter_by(parent_id=id).all()
        files = Media.query.filter_by(folder=folder.path).all()
        
        return jsonify({
            'id': folder.id,
            'name': folder.name,
            'path': folder.path,
            'subfolders': [{
                'id': f.id,
                'name': f.name,
                'path': f.path
            } for f in subfolders],
            'files': [{
                'id': f.id,
                'filename': f.original_filename,
                'url': f.url,
                'preview_url': f.preview_url
            } for f in files]
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        new_name = data.get('name')
        
        if new_name:
            new_name = secure_filename(new_name)
            new_path = os.path.join(os.path.dirname(folder.path), new_name)
            
            # Check if new path exists
            if MediaFolder.query.filter_by(path=new_path).first():
                return jsonify({'error': 'Folder with this name already exists'}), 400
            
            # Rename physical folder
            old_path = os.path.join(UPLOAD_FOLDER, folder.path)
            new_path_full = os.path.join(UPLOAD_FOLDER, new_path)
            if os.path.exists(old_path):
                os.rename(old_path, new_path_full)
            
            # Update folder and all subfolders
            old_path_prefix = folder.path + '/'
            for subfolder in MediaFolder.query.filter(MediaFolder.path.startswith(old_path_prefix)).all():
                subfolder.path = new_path + subfolder.path[len(folder.path):]
            
            # Update media files
            for media_item in Media.query.filter(Media.folder.startswith(old_path_prefix)).all():
                media_item.folder = new_path + media_item.folder[len(folder.path):]
            
            folder.name = new_name
            folder.path = new_path
            db.session.commit()
            
        return jsonify({'status': 'success'})
    
    elif request.method == 'DELETE':
        # Check if folder is empty
        if Media.query.filter_by(folder=folder.path).first():
            return jsonify({'error': 'Folder is not empty'}), 400
        
        # Delete physical folder
        folder_path = os.path.join(UPLOAD_FOLDER, folder.path)
        if os.path.exists(folder_path):
            os.rmdir(folder_path)
        
        db.session.delete(folder)
        db.session.commit()
        return jsonify({'status': 'success'})
