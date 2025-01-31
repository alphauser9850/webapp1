import click
from flask.cli import with_appcontext
from app.models import User, Category, Session
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

@click.command('create-admin')
@click.option('--username', prompt=True, help='Admin username')
@click.option('--email', prompt=True, help='Admin email')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@with_appcontext
def create_admin(username, email, password):
    """Create an admin user."""
    user = User.query.filter_by(username=username).first()
    if user:
        click.echo('User already exists. Updating to admin...')
        user.is_admin = True
        user.is_superadmin = True
    else:
        user = User(
            username=username,
            email=email,
            is_admin=True,
            is_superadmin=True,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
    
    try:
        db.session.commit()
        click.echo('Admin user created/updated successfully!')
    except Exception as e:
        click.echo(f"Failed to create/update admin user: {e}")

@click.command('reset-admin')
@with_appcontext
def reset_admin_command():
    """Reset admin user with new credentials"""
    
    # Remove existing admin's sessions first
    admin = User.query.filter_by(is_admin=True).first()
    if admin:
        # Delete associated sessions first
        Session.query.filter_by(user_id=admin.id).delete()
        db.session.commit()
        
        # Now delete the admin
        db.session.delete(admin)
        db.session.commit()
        click.echo('Existing admin user removed')

    # Create new admin user
    admin = User(
        username='admin',
        email='admin@deshmukhsystems.com',
        is_admin=True,
        is_superadmin=True,
        is_active=True
    )
    admin.set_password('admin@123')
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f"Admin user reset successfully!")
    click.echo(f"Username: admin")
    click.echo(f"Password: admin@123")

@click.command('verify-admin')
@with_appcontext
def verify_admin_command():
    """Verify admin credentials in database"""
    admin = User.query.filter_by(username='admin', is_admin=True).first()
    if not admin:
        click.echo('Admin user not found!')
        return
    
    click.echo(f"Admin user found:")
    click.echo(f"Username: {admin.username}")
    click.echo(f"Email: {admin.email}")
    click.echo(f"Is Admin: {admin.is_admin}")
    click.echo(f"Password hash: {admin.password_hash}")
    
    # Test password
    test_password = 'admin123'
    if admin.check_password(test_password):
        click.echo(f"\nPassword '{test_password}' is correct!")
    else:
        click.echo(f"\nPassword '{test_password}' is NOT correct!")

def init_app(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(reset_admin_command)
    app.cli.add_command(verify_admin_command) 