class LabTimer {
    constructor(startTime, remainingHours, sessionId, endSessionUrl, isDemo) {
        this.startTime = new Date(startTime + 'Z');
        this.remainingHours = remainingHours;
        this.sessionId = sessionId;
        this.endSessionUrl = endSessionUrl;
        this.isDemo = isDemo;
        this.timerElement = document.getElementById('timer');
        this.interval = null;
        this.lastUpdateTime = null;
        this.totalSeconds = this.isDemo ? 1800 : (this.remainingHours * 3600);
    }

    start() {
        this.lastUpdateTime = new Date();
        this.updateTimer();
        this.interval = setInterval(() => this.updateTimer(), 1000);
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }

    updateTimer() {
        const now = new Date();
        
        if (this.lastUpdateTime) {
            const elapsedSeconds = (now - this.lastUpdateTime) / 1000;
            this.totalSeconds -= elapsedSeconds;
        }
        this.lastUpdateTime = now;

        if (this.totalSeconds <= 0) {
            this.endSession();
            return;
        }

        const hours = Math.floor(this.totalSeconds / 3600);
        const minutes = Math.floor((this.totalSeconds % 3600) / 60);
        const seconds = Math.floor(this.totalSeconds % 60);

        const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        if (this.totalSeconds < 300) {
            this.timerElement.style.color = '#ff4444';
            this.timerElement.style.animation = 'blink 1s ease-in-out infinite';
        } else if (this.totalSeconds < 900) {
            this.timerElement.style.color = '#ffbb33';
            this.timerElement.style.animation = 'none';
        } else {
            this.timerElement.style.color = '#00ff00';
            this.timerElement.style.animation = 'none';
        }
        
        this.timerElement.textContent = timeString;

        if (!document.getElementById('timer-animation')) {
            const style = document.createElement('style');
            style.id = 'timer-animation';
            style.textContent = `
                @keyframes blink {
                    0% { opacity: 1; }
                    50% { opacity: 0.5; }
                    100% { opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    async endSession() {
        this.stop();
        
        try {
            const response = await fetch(this.endSessionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                window.dispatchEvent(new Event('session-end'));
                window.location.href = '/dashboard';
            } else {
                console.error('Failed to end session');
            }
        } catch (error) {
            console.error('Error ending session:', error);
        }
    }
}
