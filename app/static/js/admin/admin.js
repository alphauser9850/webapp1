// User Management
function openEditUserModal(userId) {
    fetch(`/admin/users/${userId}`)
        .then(response => response.json())
        .then(user => {
            document.getElementById('editUserId').value = user.id;
            document.getElementById('editUsername').value = user.username;
            document.getElementById('editEmail').value = user.email;
            document.getElementById('editIsActive').checked = user.is_active;
            document.getElementById('editIsAdmin').checked = user.is_admin;
            document.getElementById('editRemainingHours').value = user.remaining_hours;
            
            const modal = document.getElementById('userModal');
            modal.classList.remove('hidden');
            document.getElementById('modalTitle').textContent = 'Edit User';
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error loading user data', 'error');
        });
}

function openAddUserModal() {
    const modal = document.getElementById('userModal');
    modal.classList.remove('hidden');
    document.getElementById('modalTitle').textContent = 'Add User';
    
    // Reset form
    const form = document.getElementById('addUserForm');
    if (form) {
        form.reset();
    }
}

function submitUserForm(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const action = form.getAttribute('data-action');
    const userId = form.querySelector('input[name="user_id"]')?.value;
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    
    // Convert checkbox values to boolean strings
    formData.set('is_active', form.querySelector('input[name="is_active"]').checked ? 'true' : 'false');
    formData.set('is_admin', form.querySelector('input[name="is_admin"]').checked ? 'true' : 'false');
    
    const url = action === 'edit' ? `/admin/users/${userId}/edit` : '/admin/users/create';
    const method = action === 'edit' ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            showNotification(data.message || 'Operation successful', 'success');
            closeModal('userModal');
            // Reload the page to show updated user list
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred. Please try again.', 'error');
    });
}

// Server Management
function toggleServerStatus(serverId) {
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    fetch(`/admin/servers/${serverId}/toggle-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            
            // Update the UI immediately
            const statusCell = document.querySelector(`#server-${serverId}-status`);
            if (statusCell) {
                const statusBadge = statusCell.querySelector('span');
                if (statusBadge) {
                    if (data.is_active) {
                        statusBadge.className = 'px-2 py-1 text-xs rounded-full bg-green-500/10 text-green-400';
                        statusBadge.textContent = 'Active';
                    } else {
                        statusBadge.className = 'px-2 py-1 text-xs rounded-full bg-red-500/10 text-red-400';
                        statusBadge.textContent = 'Inactive';
                    }
                }
            }
            
            // Update the toggle button
            const toggleButton = document.querySelector(`button[onclick="toggleServerStatus('${serverId}')"]`);
            if (toggleButton) {
                const icon = toggleButton.querySelector('i');
                if (icon) {
                    icon.className = data.is_active ? 'fas fa-toggle-on' : 'fas fa-toggle-off';
                }
                toggleButton.title = data.is_active ? 'Deactivate Server' : 'Activate Server';
            }
        } else {
            showNotification(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your request.', 'error');
    });
}

// Server Management Functions
function openAddServerModal() {
    const modal = document.getElementById('serverModal');
    modal.classList.remove('hidden');
    document.getElementById('modalTitle').textContent = 'Add Server';
    
    // Reset form
    const form = document.getElementById('serverForm');
    if (form) {
        form.reset();
        form.setAttribute('data-action', 'create');
    }
}

function openEditServerModal(serverId) {
    fetch(`/admin/servers/${serverId}`)
        .then(response => response.json())
        .then(server => {
            const form = document.getElementById('serverForm');
            if (form) {
                form.setAttribute('data-action', 'edit');
                form.setAttribute('data-server-id', serverId);
                document.getElementById('serverName').value = server.name;
                document.getElementById('serverAddress').value = server.connection_address;
                document.getElementById('serverCategory').value = server.category_id;
            }
            
            const modal = document.getElementById('serverModal');
            modal.classList.remove('hidden');
            document.getElementById('modalTitle').textContent = 'Edit Server';
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error loading server data', 'error');
        });
}

function submitServerForm(event) {
    event.preventDefault();
    const form = event.target;
    const action = form.getAttribute('data-action');
    const serverId = form.getAttribute('data-server-id');
    
    const data = {
        name: document.getElementById('serverName').value,
        connection_address: document.getElementById('serverAddress').value,
        category_id: document.getElementById('serverCategory').value
    };
    
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;
    
    const url = action === 'create' ? '/admin/servers/create' : `/admin/servers/${serverId}`;
    const method = action === 'create' ? 'POST' : 'PUT';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            closeModal('serverModal');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showNotification(data.error || 'An error occurred', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while processing your request.', 'error');
    });
}

// Utility Functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        'bg-blue-500'
    } text-white`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Add form submission handlers
    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
        addUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitUserForm(e);
        });
    }

    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
        editUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const userId = document.getElementById('editUserId').value;
            submitUserForm(e);
        });
    }

    // Add modal close handlers
    const closeButtons = document.querySelectorAll('[data-modal-close]');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.dataset.modalTarget;
            closeModal(modalId);
        });
    });

    const serverForm = document.getElementById('serverForm');
    if (serverForm) {
        serverForm.addEventListener('submit', submitServerForm);
    }
}); 
