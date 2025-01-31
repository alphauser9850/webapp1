import psutil
import os
from datetime import datetime

class SystemMonitor:
    @staticmethod
    def get_system_health():
        """Get real-time system health metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024 * 1024 * 1024)  # Convert to GB
            memory_used = memory.used / (1024 * 1024 * 1024)
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_total = disk.total / (1024 * 1024 * 1024)
            disk_used = disk.used / (1024 * 1024 * 1024)
            disk_percent = disk.percent
            
            # System load (1, 5, 15 minute averages)
            load_avg = psutil.getloadavg()
            
            # System uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'core_count': cpu_count,
                    'load_average': {
                        '1min': load_avg[0],
                        '5min': load_avg[1],
                        '15min': load_avg[2]
                    }
                },
                'memory': {
                    'total_gb': round(memory_total, 2),
                    'used_gb': round(memory_used, 2),
                    'usage_percent': memory_percent
                },
                'disk': {
                    'total_gb': round(disk_total, 2),
                    'used_gb': round(disk_used, 2),
                    'usage_percent': disk_percent
                },
                'uptime': {
                    'days': uptime.days,
                    'hours': uptime.seconds // 3600,
                    'minutes': (uptime.seconds % 3600) // 60
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            } 