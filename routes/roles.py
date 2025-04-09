from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, User
from models.roles import Role, Permission, PermissionCategory, RoleAuditLog, role_permissions
from functools import wraps
import json
from datetime import datetime

roles_bp = Blueprint('roles', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_permission('access_admin_panel'):
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Role management routes
@roles_bp.route('/admin/roles')
@login_required
@admin_required
def roles_list():
    """Display list of all roles"""
    if not current_user.has_permission('view_roles'):
        flash('You do not have permission to view roles.', 'error')
        return redirect(url_for('admin.dashboard'))
        
    roles = Role.query.order_by(Role.display_order).all()
    return render_template('admin/roles/list.html', roles=roles)

@roles_bp.route('/admin/roles/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_role():
    """Create a new role"""
    if not current_user.has_permission('create_roles'):
        flash('You do not have permission to create roles.', 'error')
        return redirect(url_for('roles.roles_list'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        display_order = request.form.get('display_order', 0, type=int)
        
        # Check if role already exists
        existing_role = Role.query.filter_by(name=name).first()
        if existing_role:
            flash(f'A role with the name "{name}" already exists.', 'error')
            return redirect(url_for('roles.new_role'))
            
        # Create new role
        role = Role(
            name=name,
            description=description,
            display_order=display_order,
            is_system=False
        )
        
        # Add permissions to role
        permission_ids = request.form.getlist('permissions')
        permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
        role.permissions = permissions
        
        db.session.add(role)
        
        # Log the action
        audit_log = RoleAuditLog(
            user_id=current_user.id,
            action='create',
            entity_type='role',
            entity_id=role.id,
            details=json.dumps({
                'name': name,
                'description': description,
                'permissions': [p.name for p in permissions]
            })
        )
        db.session.add(audit_log)
        
        db.session.commit()
        flash(f'Role "{name}" created successfully.', 'success')
        return redirect(url_for('roles.roles_list'))
        
    # GET request - show form
    permissions = Permission.query.all()
    categories = PermissionCategory.query.order_by(PermissionCategory.display_order).all()
    
    # Group permissions by category
    categorized_permissions = {}
    for category in categories:
        categorized_permissions[category.name] = [p for p in permissions if p.category == category.name]
    
    return render_template('admin/roles/edit.html', 
                          role=None, 
                          permissions=permissions,
                          categories=categories,
                          categorized_permissions=categorized_permissions)

@roles_bp.route('/admin/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    """Edit an existing role"""
    if not current_user.has_permission('edit_roles'):
        flash('You do not have permission to edit roles.', 'error')
        return redirect(url_for('roles.roles_list'))
        
    role = Role.query.get_or_404(role_id)
    
    # Prevent editing system roles (except permissions)
    if role.is_system and request.method == 'POST' and request.form.get('name'):
        flash('System roles cannot be renamed or deleted.', 'error')
        return redirect(url_for('roles.roles_list'))
        
    if request.method == 'POST':
        # Get original permissions for audit log
        original_permissions = [p.name for p in role.permissions]
        
        # Only update non-system role properties
        if not role.is_system:
            role.name = request.form.get('name')
            role.description = request.form.get('description')
            role.display_order = request.form.get('display_order', 0, type=int)
        
        # Update permissions
        permission_ids = request.form.getlist('permissions')
        permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
        role.permissions = permissions
        
        # Log the action
        audit_log = RoleAuditLog(
            user_id=current_user.id,
            action='update',
            entity_type='role',
            entity_id=role.id,
            details=json.dumps({
                'name': role.name,
                'description': role.description,
                'original_permissions': original_permissions,
                'new_permissions': [p.name for p in permissions]
            })
        )
        db.session.add(audit_log)
        
        db.session.commit()
        flash(f'Role "{role.name}" updated successfully.', 'success')
        return redirect(url_for('roles.roles_list'))
        
    # GET request - show form
    permissions = Permission.query.all()
    categories = PermissionCategory.query.order_by(PermissionCategory.display_order).all()
    
    # Group permissions by category
    categorized_permissions = {}
    for category in categories:
        categorized_permissions[category.name] = [p for p in permissions if p.category == category.name]
    
    return render_template('admin/roles/edit.html', 
                          role=role, 
                          permissions=permissions,
                          categories=categories,
                          categorized_permissions=categorized_permissions)

@roles_bp.route('/admin/roles/delete/<int:role_id>', methods=['POST'])
@login_required
@admin_required
def delete_role(role_id):
    """Delete a role"""
    if not current_user.has_permission('delete_roles'):
        flash('You do not have permission to delete roles.', 'error')
        return redirect(url_for('roles.roles_list'))
        
    role = Role.query.get_or_404(role_id)
    
    # Prevent deleting system roles
    if role.is_system:
        flash('System roles cannot be deleted.', 'error')
        return redirect(url_for('roles.roles_list'))
        
    # Log the action before deletion
    audit_log = RoleAuditLog(
        user_id=current_user.id,
        action='delete',
        entity_type='role',
        entity_id=role.id,
        details=json.dumps({
            'name': role.name,
            'description': role.description,
            'permissions': [p.name for p in role.permissions]
        })
    )
    db.session.add(audit_log)
    
    # Delete the role
    db.session.delete(role)
    db.session.commit()
    
    flash(f'Role "{role.name}" deleted successfully.', 'success')
    return redirect(url_for('roles.roles_list'))

# User-Role Assignment routes
@roles_bp.route('/admin/users/<int:user_id>/roles', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user_roles(user_id):
    """Manage roles for a specific user"""
    if not current_user.has_permission('assign_roles'):
        flash('You do not have permission to assign roles.', 'error')
        return redirect(url_for('admin.users'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Get original roles for audit log
        original_roles = [r.name for r in user.roles]
        
        # Update user roles
        role_ids = request.form.getlist('roles')
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles
        
        # Log the action
        audit_log = RoleAuditLog(
            user_id=current_user.id,
            action='update',
            entity_type='user_roles',
            entity_id=user.id,
            details=json.dumps({
                'username': user.username,
                'original_roles': original_roles,
                'new_roles': [r.name for r in roles]
            })
        )
        db.session.add(audit_log)
        
        db.session.commit()
        flash(f'Roles for user "{user.username}" updated successfully.', 'success')
        return redirect(url_for('admin.users'))
        
    # GET request - show form
    roles = Role.query.order_by(Role.display_order).all()
    return render_template('admin/roles/user_roles.html', user=user, roles=roles)

# Permission management routes
@roles_bp.route('/admin/permissions')
@login_required
@admin_required
def permissions_list():
    """Display list of all permissions"""
    if not current_user.has_permission('view_roles'):
        flash('You do not have permission to view permissions.', 'error')
        return redirect(url_for('admin.dashboard'))
        
    permissions = Permission.query.all()
    categories = PermissionCategory.query.order_by(PermissionCategory.display_order).all()
    
    # Group permissions by category
    categorized_permissions = {}
    for category in categories:
        categorized_permissions[category.name] = [p for p in permissions if p.category == category.name]
    
    return render_template('admin/roles/permissions.html', 
                          permissions=permissions,
                          categories=categories,
                          categorized_permissions=categorized_permissions)

# Audit log routes
@roles_bp.route('/admin/roles/audit-log')
@login_required
@admin_required
def audit_log():
    """Display role and permission audit log"""
    if not current_user.has_permission('view_roles'):
        flash('You do not have permission to view the audit log.', 'error')
        return redirect(url_for('admin.dashboard'))
        
    logs = RoleAuditLog.query.order_by(RoleAuditLog.timestamp.desc()).all()
    return render_template('admin/roles/audit_log.html', logs=logs)

# API endpoints for AJAX operations
@roles_bp.route('/api/roles/<int:role_id>/permissions', methods=['GET'])
@login_required
@admin_required
def get_role_permissions(role_id):
    """Get permissions for a role (for AJAX)"""
    role = Role.query.get_or_404(role_id)
    permissions = [{'id': p.id, 'name': p.name} for p in role.permissions]
    return jsonify(permissions)

@roles_bp.route('/api/users/<int:user_id>/permissions', methods=['GET'])
@login_required
@admin_required
def get_user_permissions(user_id):
    """Get all permissions for a user (for AJAX)"""
    user = User.query.get_or_404(user_id)
    permissions = [{'id': p.id, 'name': p.name} for p in user.get_permissions()]
    return jsonify(permissions)
