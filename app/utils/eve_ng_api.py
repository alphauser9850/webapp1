import requests
import base64
import json
from flask import current_app
import logging
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL verification warnings
urllib3.disable_warnings(InsecureRequestWarning)

class EveNGAPI:
    def __init__(self, server):
        """Initialize EVE-NG API client.
        
        Args:
            server: Server model instance containing connection details
        """
        self.server = server
        self.base_url = f"https://{server.connection_address}/api"
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for self-signed certs
        self.cookies = None
        # Login immediately upon initialization
        self._login()
    
    def check_server_health(self):
        """Check if EVE-NG server is accessible."""
        try:
            response = self.session.get(
                f"https://{self.server.connection_address}",
                verify=False,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logging.error(f"EVE-NG server health check failed: {str(e)}")
            return False
    
    def _login(self):
        """Login to EVE-NG API using server credentials."""
        if not self.check_server_health():
            logging.error("EVE-NG server is not accessible")
            return False
            
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={
                    "username": self.server.eve_username,
                    "password": self.server.eve_password,
                    "html5": "-1"  # Required parameter for API access
                },
                headers={
                    'Content-Type': 'application/json'
                },
                verify=False,
                timeout=5
            )
            
            if response.status_code == 200:
                # Store all cookies from the response
                self.cookies = response.cookies
                # Add cookies to session
                self.session.cookies.update(self.cookies)
                return True
            
            logging.error(f"EVE-NG login failed: {response.text}")
            return False
            
        except Exception as e:
            logging.error(f"EVE-NG connection error: {str(e)}")
            return False
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make an API request with automatic re-login on auth failure."""
        try:
            response = getattr(self.session, method)(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                verify=False,
                timeout=5,
                **kwargs
            )
            
            # If unauthorized, try to re-login and retry the request
            if response.status_code == 401:
                if self._login():
                    response = getattr(self.session, method)(
                        f"{self.base_url}/{endpoint.lstrip('/')}",
                        verify=False,
                        timeout=5,
                        **kwargs
                    )
            
            return response
        except Exception as e:
            logging.error(f"API request failed: {str(e)}")
            return None
    
    def list_labs(self, folder="/"):
        """List all labs in a folder."""
        try:
            response = self._make_request(
                'get',
                'folders/',  # Updated endpoint
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': '; '.join([f"{k}={v}" for k, v in self.session.cookies.items()])
                }
            )
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    # Log the raw response for debugging
                    current_app.logger.debug(f"EVE-NG API Response: {data}")
                    
                    # Return the raw data for now to see the structure
                    return {
                        'success': True,
                        'data': data,
                        'cookies': dict(self.session.cookies)
                    }
                except json.JSONDecodeError as e:
                    current_app.logger.error(f"Failed to parse JSON response: {str(e)}")
                    return {
                        'success': False,
                        'error': 'Invalid JSON response',
                        'raw_response': response.text
                    }
            
            current_app.logger.error(f"Failed to list labs. Status: {response.status_code if response else 'No response'}")
            return {
                'success': False,
                'error': f"Request failed with status {response.status_code if response else 'No response'}",
                'response': response.text if response else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Error listing labs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_lab(self, lab_path):
        """Get lab information by path."""
        try:
            # Format the lab path correctly - ensure it ends with .unl
            if not lab_path.endswith('.unl'):
                lab_path = f"{lab_path}.unl"
            
            # Remove any leading slashes and 'labs' from the path
            lab_path = lab_path.lstrip('/').replace('labs/', '')
            
            current_app.logger.info(f"Getting lab info for path: {lab_path}")
            response = self._make_request(
                'get',
                f"labs/{lab_path}",
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if response and response.status_code == 200:
                data = response.json()
                current_app.logger.info(f"Lab info response: {data}")
                return data
            
            current_app.logger.error(f"Failed to get lab info. Status: {response.status_code if response else 'No response'}")
            if response:
                current_app.logger.error(f"Response text: {response.text}")
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error getting lab info: {str(e)}")
            return None

    def create_user(self, username, password, name=None, email=None):
        """Create a new user in EVE-NG with admin role"""
        data = {
            'username': username,
            'password': password,
            'name': name or "Eve-NG Administrator",
            'email': email or "root@localhost",
            'extauth': 'internal',
            'role': 'admin',
            'html5': -1,
        }
        
        try:
            # Log the request data
            current_app.logger.info(f"Creating EVE-NG user with data: {data}")
            
            response = self._make_request(
                'post',
                'users',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response and response.status_code in (200, 201):
                response_data = response.json() if response.headers.get('content-type') == 'application/json' else {'text': response.text}
                current_app.logger.info(f"EVE-NG user creation successful. Response: {response_data}")
                
                # Verify user was created correctly
                verify_response = self._make_request(
                    'get',
                    f'users/{username}',
                    headers={'Content-Type': 'application/json'}
                )
                if verify_response and verify_response.status_code == 200:
                    current_app.logger.info(f"User verification response: {verify_response.json()}")
                
                return True
            else:
                current_app.logger.error(f"EVE-NG user creation failed with status {response.status_code if response else 'No response'}")
                if response:
                    current_app.logger.error(f"Response text: {response.text}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Failed to create EVE-NG user: {str(e)}")
            return False

    def start_nodes(self, lab_path):
        """Start all nodes in a lab"""
        try:
            # Format the lab path correctly - ensure it ends with .unl
            if not lab_path.endswith('.unl'):
                lab_path = f"{lab_path}.unl"
            
            # Remove any leading slashes and 'labs' from the path
            lab_path = lab_path.lstrip('/').replace('labs/', '')
            
            current_app.logger.info(f"Starting all nodes in lab: {lab_path}")
            
            # Start all nodes at once
            response = self._make_request(
                'get',
                f"labs/{lab_path}/nodes/start",
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            
            if response and response.status_code == 200:
                current_app.logger.info("Successfully started all nodes")
                return True
                
            current_app.logger.error(f"Failed to start nodes. Status: {response.status_code if response else 'No response'}")
            if response:
                current_app.logger.error(f"Response text: {response.text}")
            return False
            
        except Exception as e:
            current_app.logger.error(f"Failed to start nodes: {str(e)}")
            return False

    def auto_login_and_start_lab(self, username, password, lab_path):
        """Automatically login user and start the specified lab"""
        try:
            # First login with user credentials
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={
                    "username": username,
                    "password": password,
                    "html5": "-1"  # Required parameter for API access
                },
                headers={
                    'Content-Type': 'application/json'
                },
                verify=False,
                timeout=5
            )
            
            if response.status_code != 200:
                current_app.logger.error(f"User login failed: {response.text}")
                return False
                
            # Store user's cookies
            self.session.cookies.update(response.cookies)
            
            # Get the lab
            lab = self.get_lab(lab_path)
            if not lab:
                current_app.logger.error("Failed to get lab info")
                return False
                
            # Start all nodes
            if not self.start_nodes(lab_path):
                current_app.logger.error("Failed to start nodes")
                return False
                
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to auto login and start lab: {str(e)}")
            return False

    def logout(self):
        """Logout from EVE-NG"""
        try:
            response = self._make_request(
                'get',
                'auth/logout',
                headers={'Content-Type': 'application/json'}
            )
            return response and response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"EVE-NG logout failed: {str(e)}")
            return False

    def login_user(self, username, password):
        """Login user to EVE-NG without starting a specific lab"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={
                    "username": username,
                    "password": password,
                    "html5": "-1"  # Required parameter for API access
                },
                headers={
                    'Content-Type': 'application/json'
                },
                verify=False,
                timeout=5
            )
            
            if response.status_code == 200:
                # Store all cookies from the response
                self.session.cookies.update(response.cookies)
                current_app.logger.info(f"Successfully logged in user {username} to EVE-NG")
                return True
            
            current_app.logger.error(f"EVE-NG login failed for user {username}: {response.text}")
            return False
            
        except Exception as e:
            current_app.logger.error(f"EVE-NG login error for user {username}: {str(e)}")
            return False 