from flask import Blueprint, jsonify, current_app, request
from app import db
from app.models import Server, Lab
from app.utils.eve_ng_api import EveNGAPI
from flask_login import login_required
from app.decorators import admin_required

api = Blueprint('api', __name__)

@api.route('/server/<int:server_id>/credentials', methods=['POST'])
@login_required
@admin_required
def update_credentials(server_id):
    server = Server.query.get_or_404(server_id)
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username:
        server.eve_username = username
    if password:
        server.eve_password = password
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Credentials updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating credentials: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update credentials'
        })

@api.route('/test_auth/<int:server_id>', methods=['POST'])
@login_required
@admin_required
def test_auth(server_id):
    server = Server.query.get_or_404(server_id)
    api = EveNGAPI(server)
    
    # Get credentials being used
    credentials = {
        'username': server.eve_username,
        'password': server.eve_password,  # This will be None if decryption fails
        'server_address': server.connection_address
    }
    
    # Try to login
    response = api._make_request(
        'post',
        'auth/login',
        json={
            'username': credentials['username'],
            'password': credentials['password'],
            'html5': '-1'
        },
        headers={'Content-Type': 'application/json'}
    )
    
    if response:
        response_data = response.json() if response.headers.get('content-type') == 'application/json' else {'text': response.text}
        status_code = response.status_code
    else:
        response_data = None
        status_code = None
    
    result = {
        'success': bool(response and response.status_code == 200),
        'message': 'Successfully authenticated' if (response and response.status_code == 200) else 'Failed to authenticate',
        'details': {
            'credentials_used': {
                'username': credentials['username'],
                'password': '***' if credentials['password'] else None,
                'server': credentials['server_address']
            },
            'response': {
                'status_code': status_code,
                'data': response_data
            }
        }
    }
    
    return jsonify(result)

@api.route('/list_labs/<int:server_id>', methods=['GET'])
@login_required
@admin_required
def list_labs(server_id):
    server = Server.query.get_or_404(server_id)
    api = EveNGAPI(server)
    
    if not api._login():
        return jsonify({
            'success': False,
            'message': 'Failed to authenticate with EVE-NG server'
        })
    
    labs = api.list_labs()
    if labs:
        return jsonify({
            'success': True,
            'message': 'Successfully retrieved labs',
            'data': labs
        })
    
    return jsonify({
        'success': False,
        'message': 'No labs found or error retrieving labs'
    })

@api.route('/import_labs/<int:server_id>', methods=['POST'])
@login_required
@admin_required
def import_labs(server_id):
    server = Server.query.get_or_404(server_id)
    api = EveNGAPI(server)
    
    if not api._login():
        return jsonify({
            'success': False,
            'message': 'Failed to authenticate with EVE-NG server'
        })
    
    # Get labs from EVE-NG
    labs_response = api.list_labs()
    
    try:
        # Navigate the nested structure correctly
        labs = labs_response.get('data', {}).get('data', {}).get('data', {}).get('labs', [])
        
        if not isinstance(labs, list):
            current_app.logger.error(f"Labs data is not a list: {labs}")
            return jsonify({
                'success': False,
                'message': 'Invalid labs data format',
                'debug_data': {
                    'labs_response': labs_response,
                    'labs_data': labs
                }
            })
        
        if not labs:
            return jsonify({
                'success': False,
                'message': 'No labs found in the root folder',
                'debug_data': {
                    'labs_response': labs_response
                }
            })
        
        imported_count = 0
        updated_count = 0
        processed_labs = []
        
        current_app.logger.info(f"Processing {len(labs)} labs")
        
        for lab_data in labs:
            # Extract lab details
            lab_path = lab_data.get('path')
            lab_name = lab_data.get('file', '').replace('.unl', '')
            
            current_app.logger.info(f"Processing lab: {lab_name} at {lab_path}")
            
            if not lab_path or not lab_name:
                current_app.logger.warning(f"Skipping lab with invalid data: {lab_data}")
                continue
            
            try:
                # Check if lab already exists
                existing_lab = Lab.query.filter_by(
                    server_id=server.id,
                    lab_path=lab_path
                ).first()
                
                if existing_lab:
                    # Update existing lab
                    existing_lab.name = lab_name
                    existing_lab.modified_at = lab_data.get('mtime', '')
                    updated_count += 1
                    processed_labs.append({
                        'name': lab_name,
                        'path': lab_path,
                        'action': 'updated'
                    })
                    current_app.logger.info(f"Updated lab: {lab_name}")
                else:
                    # Create new lab
                    new_lab = Lab(
                        name=lab_name,
                        lab_path=lab_path,
                        server_id=server.id,
                        modified_at=lab_data.get('mtime', '')
                    )
                    db.session.add(new_lab)
                    imported_count += 1
                    processed_labs.append({
                        'name': lab_name,
                        'path': lab_path,
                        'action': 'imported'
                    })
                    current_app.logger.info(f"Imported new lab: {lab_name}")
            
            except Exception as lab_error:
                current_app.logger.error(f"Error processing lab {lab_name}: {str(lab_error)}")
                continue
        
        db.session.commit()
        current_app.logger.info(f"Successfully processed all labs. Imported: {imported_count}, Updated: {updated_count}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} new labs and updated {updated_count} existing labs',
            'data': {
                'imported': imported_count,
                'updated': updated_count,
                'total': len(labs),
                'processed_labs': processed_labs
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error importing labs: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error importing labs: {str(e)}',
            'details': {
                'error': str(e),
                'response_data': labs_response
            }
        }) 