from flask import Blueprint, render_template
from flask_login import login_required, current_user
from functools import wraps

network_admin = Blueprint('network_admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return render_template('errors/403.html'), 403
        return f(*args, **kwargs)
    return decorated_function

@network_admin.route('/network-admin')
@login_required
@admin_required
def network_dashboard():
    return render_template('network_admin/dashboard.html') 