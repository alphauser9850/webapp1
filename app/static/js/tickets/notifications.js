// Initialize Socket.IO with connection options
const socket = io({
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5
});

// Get current user ID from the page
const currentUserId = parseInt(document.body.getAttribute('data-user-id'), 10);
const isAdmin = document.body.getAttribute('data-is-admin') === 'true';
let unreadCount = 0;
const originalTitle = document.title;

// Socket connection events with logging
socket.on('connect', () => {
    console.log('Connected to WebSocket');
    if (currentUserId) {
        socket.emit('join', { room: `user_${currentUserId}` });
        console.log(`Joined user room: user_${currentUserId}`);
        
        socket.emit('join', { room: 'dashboard' });
        console.log('Joined dashboard room');
        
        if (isAdmin) {
            socket.emit('join', { room: 'admin_notifications' });
            console.log('Joined admin notifications room');
        }
    }
});

socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket');
});

// Event handlers for different notification types
socket.on('new_message', (data) => {
    console.log('Received new_message:', data);
    if (!data.message || !data.ticket_id) return;
    
    const messageUserId = data.message.user_id || data.user_id;
    if (messageUserId && messageUserId !== currentUserId) {
        updateCounters();
    }
});

socket.on('ticket_update', (data) => {
    console.log('Received ticket_update:', data);
    if (!data.ticket) return;
    
    if (data.update_type === 'message') {
        const senderId = data.user_id || (data.message && data.message.user_id);
        if (senderId !== currentUserId) {
            updateCounters();
        }
    }
});

socket.on('ticket_status_change', (data) => {
    console.log('Received status_change:', data);
    if (!data.ticket) return;
    updateCounters();
});

socket.on('new_notification', (data) => {
    console.log('Received new_notification:', data);
    if (!data.ticket) return;
    updateCounters();
});

// Utility functions
function updateCounters() {
    unreadCount++;
    
    // Update badge
    const badge = document.getElementById('notification-badge');
    if (badge) {
        badge.textContent = unreadCount;
        badge.style.display = unreadCount > 0 ? 'inline' : 'none';
    }
    
    // Update page title
    document.title = unreadCount > 0 ? `(${unreadCount}) ${originalTitle}` : originalTitle;
}

// Reset counters when page becomes visible
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        unreadCount = 0;
        document.title = originalTitle;
        const badge = document.getElementById('notification-badge');
        if (badge) {
            badge.style.display = 'none';
        }
    }
}); 