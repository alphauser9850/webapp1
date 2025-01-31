import requests
from threading import Thread
from time import sleep
import subprocess
import platform
from app import db

class ServerMonitor:
    def __init__(self, app):
        self.app = app
        self.check_interval = 300  # 5 minutes
        self.hypervisors = {
            'proxmox': {
                'ip': '192.168.1.10',
                'port': 8006,
                'type': 'proxmox'
            },
            'esxi': {
                'ip': '192.168.1.111',
                'port': 443,
                'type': 'esxi'
            }
        }

    def start_monitoring(self):
        thread = Thread(target=self._monitor_servers)
        thread.daemon = True
        thread.start()

    def check_server_ping(self, ip):
        """Check if server responds to ping"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip]
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

    def check_hypervisor_status(self, hypervisor):
        """Check hypervisor status and get metrics"""
        try:
            # First check if server responds to ping
            if not self.check_server_ping(hypervisor['ip']):
                return {
                    'online': False,
                    'cpu_usage': 0,
                    'memory_usage': 0
                }

            # For production, implement actual API calls to Proxmox/ESXi
            # This is a placeholder that returns random values
            import random
            return {
                'online': True,
                'cpu_usage': random.randint(10, 90),
                'memory_usage': random.randint(20, 85)
            }
        except Exception as e:
            print(f"Error checking hypervisor {hypervisor['ip']}: {str(e)}")
            return {
                'online': False,
                'cpu_usage': 0,
                'memory_usage': 0
            }

    def _monitor_servers(self):
        """Monitor both VM servers and physical hypervisors"""
        while True:
            with self.app.app_context():
                try:
                    # Monitor VM servers
                    from app.models.server import Server
                    servers = Server.query.all()
                    for server in servers:
                        try:
                            server.is_active = self.check_server_ping(server.ip_address)
                            db.session.commit()
                        except Exception as e:
                            print(f"Error monitoring VM server {server.ip_address}: {str(e)}")
                            server.is_active = False
                            db.session.commit()

                    # Monitor physical hypervisors
                    for hypervisor in self.hypervisors.values():
                        status = self.check_hypervisor_status(hypervisor)
                        # In production, you would store these metrics in the database
                        print(f"Hypervisor {hypervisor['ip']} status: {status}")

                except Exception as e:
                    print(f"Error in monitoring loop: {str(e)}")

            sleep(self.check_interval) 