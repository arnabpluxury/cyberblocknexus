from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models.content import BlogPost, Resource, Announcement, Page
from app import db
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import re
from functools import wraps

content = Blueprint('content', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

@content.route('/admin/blog')
@login_required
@admin_required
def blog_posts():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/content/blog_posts.html', posts=posts)

@content.route('/admin/blog/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        slug = request.form.get('slug') or slugify(title)
        post = BlogPost(
            title=title,
            slug=slug,
            content=request.form['content'],
            excerpt=request.form.get('excerpt'),
            author_id=current_user.id,
            published='publish' in request.form,
            featured='featured' in request.form,
            tags=request.form.get('tags')
        )
        db.session.add(post)
        db.session.commit()
        flash('Blog post created successfully', 'success')
        return redirect(url_for('content.blog_posts'))
    return render_template('admin/content/edit_post.html')

@content.route('/admin/blog/<int:post_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.slug = request.form.get('slug') or slugify(post.title)
        post.content = request.form['content']
        post.excerpt = request.form.get('excerpt')
        post.published = 'publish' in request.form
        post.featured = 'featured' in request.form
        post.tags = request.form.get('tags')
        db.session.commit()
        flash('Blog post updated successfully', 'success')
        return redirect(url_for('content.blog_posts'))
    return render_template('admin/content/edit_post.html', post=post)

@content.route('/admin/resources')
@login_required
@admin_required
def resources():
    resources = Resource.query.order_by(Resource.created_at.desc()).all()
    return render_template('admin/content/resources.html', resources=resources)

@content.route('/admin/resource/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_resource():
    if request.method == 'POST':
        resource = Resource(
            title=request.form['title'],
            description=request.form['description'],
            category=request.form['category'],
            type=request.form['type'],
            url=request.form.get('url'),
            author_id=current_user.id,
            published='publish' in request.form
        )
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join('uploads', 'resources', filename)
                file.save(file_path)
                resource.file_path = file_path
        
        db.session.add(resource)
        db.session.commit()
        flash('Resource created successfully', 'success')
        return redirect(url_for('content.resources'))
    return render_template('admin/content/edit_resource.html')

@content.route('/admin/announcements')
@login_required
@admin_required
def announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/content/announcements.html', announcements=announcements)

@content.route('/admin/announcement/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_announcement():
    if request.method == 'POST':
        announcement = Announcement(
            title=request.form['title'],
            content=request.form['content'],
            priority=request.form['priority'],
            author_id=current_user.id,
            active='active' in request.form
        )
        if request.form.get('expires_at'):
            announcement.expires_at = datetime.strptime(request.form['expires_at'], '%Y-%m-%dT%H:%M')
        
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully', 'success')
        return redirect(url_for('content.announcements'))
    return render_template('admin/content/edit_announcement.html')

@content.route('/admin/pages')
@login_required
@admin_required
def pages():
    pages = Page.query.order_by(Page.menu_order).all()
    return render_template('admin/content/pages.html', pages=pages)

@content.route('/admin/page/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_page():
    if request.method == 'POST':
        title = request.form['title']
        slug = request.form.get('slug') or slugify(title)
        page = Page(
            title=title,
            slug=slug,
            content=request.form['content'],
            author_id=current_user.id,
            published='publish' in request.form,
            menu_order=request.form.get('menu_order', 0),
            parent_id=request.form.get('parent_id')
        )
        db.session.add(page)
        db.session.commit()
        flash('Page created successfully', 'success')
        return redirect(url_for('content.pages'))
    return render_template('admin/content/edit_page.html')

# API endpoints for AJAX operations
@content.route('/admin/api/post/<int:post_id>/toggle-publish', methods=['POST'])
@login_required
@admin_required
def toggle_post_publish(post_id):
    post = BlogPost.query.get_or_404(post_id)
    post.published = not post.published
    db.session.commit()
    return jsonify({'status': 'success', 'published': post.published})

@content.route('/admin/api/announcement/<int:announcement_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.active = not announcement.active
    db.session.commit()
    return jsonify({'status': 'success', 'active': announcement.active})
