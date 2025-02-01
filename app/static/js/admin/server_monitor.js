class ServerMonitor {
    constructor() {
        this.servers = {
            proxmox: {
                ip: '192.168.1.10',
                name: 'Proxmox',
                elements: {
                    status: document.getElementById('proxmox-status'),
                    cpu: document.getElementById('proxmox-cpu'),
                    memory: document.getElementById('proxmox-memory')
                }
            },
            esxi: {
                ip: '192.168.1.111',
                name: 'ESXi',
                elements: {
                    status: document.getElementById('esxi-status'),
                    cpu: document.getElementById('esxi-cpu'),
                    memory: document.getElementById('esxi-memory')
                }
            }
        };

        this.updateInterval = 30000; // Update every 30 seconds
        this.startMonitoring();
    }

    async checkServerStatus(server) {
        try {
            const response = await fetch(`/admin/check_server_status?ip=${server.ip}`);
            const data = await response.json();
            
            // Update status
            server.elements.status.textContent = data.online ? 'Online' : 'Offline';
            server.elements.status.className = `badge ${data.online ? 'bg-success' : 'bg-danger'}`;
            
            // Update metrics if server is online
            if (data.online) {
                server.elements.cpu.style.width = `${data.cpu_usage}%`;
                server.elements.memory.style.width = `${data.memory_usage}%`;
                
                // Add tooltips
                server.elements.cpu.title = `CPU Usage: ${data.cpu_usage}%`;
                server.elements.memory.title = `Memory Usage: ${data.memory_usage}%`;
            } else {
                server.elements.cpu.style.width = '0%';
                server.elements.memory.style.width = '0%';
            }
        } catch (error) {
            console.error(`Error monitoring ${server.name}:`, error);
            server.elements.status.textContent = 'Error';
            server.elements.status.className = 'badge bg-warning';
        }
    }

    startMonitoring() {
        // Initial check
        Object.values(this.servers).forEach(server => this.checkServerStatus(server));
        
        // Set up periodic monitoring
        setInterval(() => {
            Object.values(this.servers).forEach(server => this.checkServerStatus(server));
        }, this.updateInterval);
    }
}

// Initialize monitoring when document is ready
document.addEventListener('DOMContentLoaded', () => {
    new ServerMonitor();
});

function updateSystemHealth() {
    fetch('/admin/system_health')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'healthy') {
                // Update CPU metrics
                const cpuBar = document.querySelector('#system-health .progress-bar-blue');
                cpuBar.style.width = `${data.cpu.usage_percent}%`;
                cpuBar.setAttribute('aria-valuenow', data.cpu.usage_percent);
                cpuBar.textContent = `CPU: ${data.cpu.usage_percent}%`;

                // Update Memory metrics
                const memoryBar = document.querySelector('#system-health .progress-bar-yellow');
                memoryBar.style.width = `${data.memory.usage_percent}%`;
                memoryBar.setAttribute('aria-valuenow', data.memory.usage_percent);
                memoryBar.textContent = `Memory: ${data.memory.usage_percent}%`;

                // Update Storage metrics
                const storageBar = document.querySelector('#system-health .progress-bar-red');
                storageBar.style.width = `${data.disk.usage_percent}%`;
                storageBar.setAttribute('aria-valuenow', data.disk.usage_percent);
                storageBar.textContent = `Storage: ${data.disk.usage_percent}%`;

                // Update uptime
                const uptimeText = document.querySelector('#system-uptime');
                if (uptimeText) {
                    uptimeText.textContent = `Uptime: ${data.uptime.days}d ${data.uptime.hours}h ${data.uptime.minutes}m`;
                }

                // Update load averages
                const loadText = document.querySelector('#system-load');
                if (loadText) {
                    loadText.textContent = `Load Avg: ${data.cpu.load_average['1min'].toFixed(2)}, ${data.cpu.load_average['5min'].toFixed(2)}, ${data.cpu.load_average['15min'].toFixed(2)}`;
                }
            }
        })
        .catch(error => console.error('Error updating system health:', error));
}

// Update system health metrics every 5 seconds
setInterval(updateSystemHealth, 5000);
// Initial update
updateSystemHealth(); 