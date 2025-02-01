import click
from flask.cli import with_appcontext
from app import db
from app.models import User, Category, Session
from werkzeug.security import generate_password_hash, check_password_hash

@click.command('create-admin')
@click.option('--email', required=True, help='Admin user email')
@click.option('--password', required=True, help='Admin user password')
@with_appcontext
def create_admin(email, password):
    """Create an admin user."""
    try:
        user = User.query.filter_by(email=email).first()
        if user:
            click.echo('Admin user already exists')
            return

        user = User(
            username=email.split('@')[0],
            email=email,
            is_admin=True,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo('Admin user created successfully')
    except Exception as e:
        click.echo(f'Error creating admin user: {str(e)}')

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