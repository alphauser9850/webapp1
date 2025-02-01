class TicketStatusManager {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.ticketId = this.form?.dataset.ticketId;
        this.statusSelect = this.form?.querySelector('select');
        this.previousStatus = this.statusSelect?.dataset.previous;
        this.isUpdating = false;

        if (this.form && this.statusSelect && this.ticketId) {
            this.initializeEventListeners();
        }
    }

    initializeEventListeners() {
        this.statusSelect.addEventListener('change', async (e) => {
            if (this.isUpdating) {
                e.preventDefault();
                return;
            }
            await this.handleStatusChange(e);
        });
    }

    async handleStatusChange(event) {
        this.isUpdating = true;
        const formData = new FormData(this.form);

        try {
            const response = await fetch(`/support/ticket/${this.ticketId}/status`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.updateUI(data);
                this.previousStatus = data.status;
                this.showToast('Success', 'Status updated successfully', 'success');
            } else {
                this.handleError(data.error || 'Failed to update status');
            }
        } catch (error) {
            console.error('Error:', error);
            this.handleError('An error occurred while updating the status');
        } finally {
            this.isUpdating = false;
        }
    }

    updateUI(data) {
        // Add system message
        if (typeof window.addMessage === 'function') {
            window.addMessage({
                content: data.message,
                is_system_message: true,
                created_at: new Date().toISOString()
            }, false);
        }

        // Update status badge
        const statusBadge = document.querySelector('.badge');
        if (statusBadge) {
            statusBadge.className = `badge bg-${data.status_color}`;
            statusBadge.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
        }
    }

    handleError(errorMessage) {
        // Revert to previous status
        if (this.statusSelect) {
            this.statusSelect.value = this.previousStatus;
        }
        this.showToast('Error', errorMessage, 'danger');
    }

    showToast(title, message, type = 'primary') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast bg-${type === 'danger' ? 'danger text-white' : 'light'}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('data-bs-delay', '5000');
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    const statusForm = document.getElementById('statusForm');
    if (statusForm) {
        new TicketStatusManager('statusForm');
    }
}); 