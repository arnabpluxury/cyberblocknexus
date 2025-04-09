from app import app, db
from models.roles import Role, Permission, PermissionCategory
from models import User
from datetime import datetime

def init_permission_categories():
    """Initialize permission categories"""
    categories = [
        {"name": "General", "description": "General site permissions", "display_order": 1},
        {"name": "Admin Panel", "description": "Admin panel access permissions", "display_order": 2},
        {"name": "Users", "description": "User management permissions", "display_order": 3},
        {"name": "Roles", "description": "Role management permissions", "display_order": 4},
        {"name": "CTF", "description": "CTF management permissions", "display_order": 5},
        {"name": "Events", "description": "Event management permissions", "display_order": 6},
        {"name": "Content", "description": "Content management permissions", "display_order": 7},
        {"name": "Media", "description": "Media management permissions", "display_order": 8},
    ]
    
    for category_data in categories:
        category = PermissionCategory.query.filter_by(name=category_data["name"]).first()
        if not category:
            category = PermissionCategory(**category_data)
            db.session.add(category)
    
    db.session.commit()
    return {c.name: c for c in PermissionCategory.query.all()}

def init_permissions(categories):
    """Initialize default permissions"""
    permissions = [
        # General permissions
        {"name": "view_site", "description": "Can view the site", "category": "General", "is_system": True},
        {"name": "participate_ctf", "description": "Can participate in CTF challenges", "category": "General", "is_system": True},
        {"name": "register_events", "description": "Can register for events", "category": "General", "is_system": True},
        
        # Admin panel permissions
        {"name": "access_admin_panel", "description": "Can access the admin panel", "category": "Admin Panel", "is_system": True},
        {"name": "view_dashboard", "description": "Can view admin dashboard", "category": "Admin Panel", "is_system": True},
        
        # User management permissions
        {"name": "view_users", "description": "Can view user list", "category": "Users", "is_system": True},
        {"name": "edit_users", "description": "Can edit user details", "category": "Users", "is_system": True},
        {"name": "delete_users", "description": "Can delete users", "category": "Users", "is_system": True},
        {"name": "ban_users", "description": "Can ban users", "category": "Users", "is_system": True},
        
        # Role management permissions
        {"name": "view_roles", "description": "Can view roles", "category": "Roles", "is_system": True},
        {"name": "create_roles", "description": "Can create new roles", "category": "Roles", "is_system": True},
        {"name": "edit_roles", "description": "Can edit roles", "category": "Roles", "is_system": True},
        {"name": "delete_roles", "description": "Can delete roles", "category": "Roles", "is_system": True},
        {"name": "assign_roles", "description": "Can assign roles to users", "category": "Roles", "is_system": True},
        
        # CTF permissions
        {"name": "view_challenges", "description": "Can view CTF challenges in admin panel", "category": "CTF", "is_system": True},
        {"name": "create_challenges", "description": "Can create CTF challenges", "category": "CTF", "is_system": True},
        {"name": "edit_challenges", "description": "Can edit CTF challenges", "category": "CTF", "is_system": True},
        {"name": "delete_challenges", "description": "Can delete CTF challenges", "category": "CTF", "is_system": True},
        
        # Event permissions
        {"name": "view_events_admin", "description": "Can view events in admin panel", "category": "Events", "is_system": True},
        {"name": "create_events", "description": "Can create events", "category": "Events", "is_system": True},
        {"name": "edit_events", "description": "Can edit events", "category": "Events", "is_system": True},
        {"name": "delete_events", "description": "Can delete events", "category": "Events", "is_system": True},
        
        # Content permissions
        {"name": "manage_content", "description": "Can manage site content", "category": "Content", "is_system": True},
        {"name": "publish_content", "description": "Can publish content", "category": "Content", "is_system": True},
        
        # Media permissions
        {"name": "upload_media", "description": "Can upload media files", "category": "Media", "is_system": True},
        {"name": "manage_media", "description": "Can manage media library", "category": "Media", "is_system": True},
    ]
    
    for perm_data in permissions:
        category_name = perm_data.pop("category")
        category = categories.get(category_name)
        
        if category:
            perm_data["category"] = category_name
            
            permission = Permission.query.filter_by(name=perm_data["name"]).first()
            if not permission:
                permission = Permission(**perm_data)
                db.session.add(permission)
    
    db.session.commit()
    return {p.name: p for p in Permission.query.all()}

def init_roles(permissions):
    """Initialize default roles"""
    roles = [
        {
            "name": "Administrator",
            "description": "Full access to all features",
            "is_system": True,
            "display_order": 1,
            "permissions": [p for p in permissions.values()]
        },
        {
            "name": "Moderator",
            "description": "Can moderate users and content",
            "is_system": True,
            "display_order": 2,
            "permissions": [
                permissions["view_site"],
                permissions["participate_ctf"],
                permissions["register_events"],
                permissions["access_admin_panel"],
                permissions["view_dashboard"],
                permissions["view_users"],
                permissions["ban_users"],
                permissions["view_challenges"],
                permissions["view_events_admin"],
                permissions["manage_content"],
            ]
        },
        {
            "name": "CTF Admin",
            "description": "Can manage CTF challenges",
            "is_system": True,
            "display_order": 3,
            "permissions": [
                permissions["view_site"],
                permissions["participate_ctf"],
                permissions["register_events"],
                permissions["access_admin_panel"],
                permissions["view_dashboard"],
                permissions["view_challenges"],
                permissions["create_challenges"],
                permissions["edit_challenges"],
                permissions["delete_challenges"],
            ]
        },
        {
            "name": "Event Manager",
            "description": "Can manage events",
            "is_system": True,
            "display_order": 4,
            "permissions": [
                permissions["view_site"],
                permissions["participate_ctf"],
                permissions["register_events"],
                permissions["access_admin_panel"],
                permissions["view_dashboard"],
                permissions["view_events_admin"],
                permissions["create_events"],
                permissions["edit_events"],
                permissions["delete_events"],
            ]
        },
        {
            "name": "Content Editor",
            "description": "Can edit and publish content",
            "is_system": True,
            "display_order": 5,
            "permissions": [
                permissions["view_site"],
                permissions["participate_ctf"],
                permissions["register_events"],
                permissions["access_admin_panel"],
                permissions["view_dashboard"],
                permissions["manage_content"],
                permissions["publish_content"],
                permissions["upload_media"],
                permissions["manage_media"],
            ]
        },
        {
            "name": "Registered User",
            "description": "Standard user permissions",
            "is_system": True,
            "display_order": 6,
            "permissions": [
                permissions["view_site"],
                permissions["participate_ctf"],
                permissions["register_events"],
            ]
        }
    ]
    
    for role_data in roles:
        role_perms = role_data.pop("permissions")
        
        role = Role.query.filter_by(name=role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
            db.session.flush()  # Flush to get the role ID
            
            # Add permissions to role
            for perm in role_perms:
                if perm not in role.permissions:
                    role.permissions.append(perm)
        else:
            # Update existing role permissions
            for perm in role_perms:
                if perm not in role.permissions:
                    role.permissions.append(perm)
    
    db.session.commit()
    return {r.name: r for r in Role.query.all()}

def assign_roles_to_existing_users(roles):
    """Assign appropriate roles to existing users"""
    # Assign Administrator role to all admin users
    admin_users = User.query.filter_by(is_admin=True).all()
    admin_role = roles["Administrator"]
    
    for user in admin_users:
        if admin_role not in user.roles:
            user.roles.append(admin_role)
    
    # Assign Registered User role to all non-admin users
    regular_users = User.query.filter_by(is_admin=False).all()
    user_role = roles["Registered User"]
    
    for user in regular_users:
        if user_role not in user.roles:
            user.roles.append(user_role)
    
    db.session.commit()

def init_all():
    """Initialize all roles and permissions"""
    with app.app_context():
        print("Initializing permission categories...")
        categories = init_permission_categories()
        
        print("Initializing permissions...")
        permissions = init_permissions(categories)
        
        print("Initializing roles...")
        roles = init_roles(permissions)
        
        print("Assigning roles to existing users...")
        assign_roles_to_existing_users(roles)
        
        print("Roles and permissions initialization complete!")

if __name__ == "__main__":
    init_all()
