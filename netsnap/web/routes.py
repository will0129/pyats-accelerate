from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import csv
from io import StringIO, BytesIO

from . import db
from .models import User
from .forms import LoginForm, ChangePasswordForm, AddUserForm, UploadInventoryForm, CaptureForm, ValidateForm

# Import netsnap core functions
from netsnap.inventory_parser import parse_inventory
from netsnap.testbed_generator import generate_testbed
from netsnap.snapshot_collector import capture_snapshot
from netsnap.comparator import compare_snapshots
# Note: Reporting via web might need logic to read JSONs and pass to template

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)

# --- Auth Routes ---

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        if user.must_change_password:
            return redirect(url_for('auth.change_password'))
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
             flash('Incorrect current password')
             return redirect(url_for('auth.change_password'))
        current_user.set_password(form.new_password.data)
        current_user.must_change_password = False
        db.session.commit()
        flash('Your password has been updated.')
        return redirect(url_for('main.dashboard'))
    return render_template('change_password.html', title='Change Password', form=form)

# --- Admin Routes ---

@admin_bp.route('/admin/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied.')
        return redirect(url_for('main.dashboard'))
    
    form = AddUserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} added.')
        return redirect(url_for('admin.manage_users'))
        
    users = User.query.all()
    return render_template('admin_users.html', title='Manage Users', form=form, users=users)

# --- Main Routes ---

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.must_change_password:
        return redirect(url_for('auth.change_password'))
        
    # List snapshots
    snapshots_dir = 'snapshots'
    snapshots = []
    if os.path.exists(snapshots_dir):
        snapshots = [d for d in os.listdir(snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d))]
        snapshots.sort(reverse=True) # Newest first
    
    return render_template('dashboard.html', title='Dashboard', snapshots=snapshots)

@main_bp.route('/inventory/download-template')
@login_required
def download_template():
    # Generate a CSV info string
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['hostname', 'ip', 'role'])
    cw.writerow(['example-router', '10.0.0.1', 'router'])
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='inventory_template.csv')

@main_bp.route('/inventory/upload', methods=['GET', 'POST'])
@login_required
def upload_inventory():
    if current_user.role == 'readonly':
        flash('Read-only users cannot modify inventory.')
        return redirect(url_for('main.dashboard'))
        
    form = UploadInventoryForm()
    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        # Save temporally
        filepath = os.path.join('uploads', filename)
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        f.save(filepath)
        
        try:
            # Init testbed
            data = parse_inventory(filepath)
            generate_testbed(data, 'testbed.yaml')
            flash('Inventory uploaded and testbed initialized successfully.')
        except Exception as e:
            flash(f'Error processing inventory: {str(e)}')
            
        return redirect(url_for('main.dashboard'))
    return render_template('upload_inventory.html', title='Upload Inventory', form=form)

@main_bp.route('/capture', methods=['GET', 'POST'])
@login_required
def capture():
    # Assuming 'readonly' CAN capture? Prompt says "execute tests".
    # Capturing is executing a test/collection.
    
    form = CaptureForm()
    if form.validate_on_submit():
        if not os.path.exists('testbed.yaml'):
             flash('No testbed initialized. Please upload inventory first.')
             return redirect(url_for('main.dashboard'))
             
        try:
             # This runs in foreground, might block. For MVP fine, ideally Async.
             snapshot_path = capture_snapshot('testbed.yaml', form.snapshot_name.data)
             flash(f'Snapshot captured: {snapshot_path}')
        except Exception as e:
             flash(f'Error capturing snapshot: {str(e)}')
        return redirect(url_for('main.dashboard'))
        
    return render_template('capture.html', title='Capture Snapshot', form=form)

@main_bp.route('/validate', methods=['GET', 'POST'])
@login_required
def validate():
    form = ValidateForm()
    # Populate baseline choices
    snapshots_dir = 'snapshots'
    choices = []
    if os.path.exists(snapshots_dir):
        dirs = [d for d in os.listdir(snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d))]
        dirs.sort(reverse=True)
        choices = [(d, d) for d in dirs]
    form.baseline_id.choices = choices
    
    if form.validate_on_submit():
        if not os.path.exists('testbed.yaml'):
             flash('No testbed initialized.')
             return redirect(url_for('main.dashboard'))
             
        baseline_path = os.path.join('snapshots', form.baseline_id.data)
        
        try:
            # 1. Capture current state
            current_name = 'validation_run'
            current_path = capture_snapshot('testbed.yaml', current_name)
            
            # 2. Compare
            diff_report = compare_snapshots(baseline_path, current_path)
            
            # 3. Render Report
            return render_template('report.html', title='Validation Report', report=diff_report)
            
        except Exception as e:
            flash(f'Error during validation: {str(e)}')
            return redirect(url_for('main.dashboard'))

    return render_template('validate.html', title='Validate State', form=form)

@main_bp.route('/report/<path:baseline>/<path:current>')
@login_required
def view_report(baseline, current):
    # Retrieve a past comparison? 
    # For now, just re-run comparison on two existing folders
    try:
        baseline_path = os.path.join('snapshots', baseline)
        current_path = os.path.join('snapshots', current)
        diff_report = compare_snapshots(baseline_path, current_path)
        return render_template('report.html', title='Comparison Report', report=diff_report)
    except Exception as e:
        flash(f'Error generating report: {str(e)}')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/help')
def help_page():
    return render_template('help.html', title='Help')

# Load user handler
from . import login_manager
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
