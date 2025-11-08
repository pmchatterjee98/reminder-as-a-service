// RAAS Mobile Notifications System

class RAASNotifications {
  constructor() {
    this.permission = 'default';
    this.notificationSchedule = new Map(); // Track scheduled notifications
  }

  // Initialize notifications and service worker
  async init() {
    // Check if browser supports notifications
    if (!('Notification' in window)) {
      console.log('This browser does not support notifications');
      return false;
    }

    // Register service worker
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/static/service-worker.js', {
          scope: '/'
        });
        console.log('Service Worker registered:', registration);
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }

    this.permission = Notification.permission;
    return this.permission === 'granted';
  }

  // Request notification permission
  async requestPermission() {
    if (!('Notification' in window)) {
      return false;
    }

    if (this.permission === 'granted') {
      return true;
    }

    try {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      return permission === 'granted';
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  // Check and schedule notifications for tasks < 24 hours
  async checkAndScheduleTasks(tasks) {
    if (this.permission !== 'granted') {
      return;
    }

    const now = new Date();
    const twentyFourHoursFromNow = new Date(now.getTime() + 24 * 60 * 60 * 1000);

    // Clear old scheduled notifications
    this.notificationSchedule.forEach((timeoutId, taskId) => {
      if (!tasks.find(t => t.id === taskId)) {
        clearTimeout(timeoutId);
        this.notificationSchedule.delete(taskId);
      }
    });

    // Schedule notifications for tasks due within 24 hours
    tasks.forEach(task => {
      if (task.completed) {
        return; // Skip completed tasks
      }

      const dueDate = new Date(task.due_date);
      
      // Check if task is due within 24 hours
      if (dueDate > now && dueDate <= twentyFourHoursFromNow) {
        // Calculate when to show notification (1 hour before due time, or immediately if <1 hour left)
        const oneHourBefore = new Date(dueDate.getTime() - 60 * 60 * 1000);
        const notificationTime = oneHourBefore > now ? oneHourBefore : now;
        const delay = notificationTime.getTime() - now.getTime();

        // Only schedule if not already scheduled
        if (!this.notificationSchedule.has(task.id)) {
          const timeoutId = setTimeout(() => {
            this.showNotification(task);
            this.notificationSchedule.delete(task.id);
          }, delay);

          this.notificationSchedule.set(task.id, timeoutId);
          console.log(`Scheduled notification for task "${task.title}" at ${notificationTime}`);
        }
      }
    });
  }

  // Show a notification for a task
  showNotification(task) {
    if (this.permission !== 'granted') {
      return;
    }

    const dueDate = new Date(task.due_date);
    const now = new Date();
    const hoursLeft = Math.round((dueDate - now) / (1000 * 60 * 60));
    const minutesLeft = Math.round((dueDate - now) / (1000 * 60));

    let timeText;
    if (hoursLeft >= 1) {
      timeText = `Due in ${hoursLeft} hour${hoursLeft > 1 ? 's' : ''}`;
    } else if (minutesLeft > 0) {
      timeText = `Due in ${minutesLeft} minute${minutesLeft > 1 ? 's' : ''}`;
    } else {
      timeText = 'Due now!';
    }

    const priorityEmoji = task.priority === 'High' ? '🔴' : task.priority === 'Medium' ? '🟡' : '🟢';

    const options = {
      body: `${priorityEmoji} ${timeText}\n${task.description || 'No description'}`,
      icon: '/static/icon-192.png',
      badge: '/static/icon-72.png',
      vibrate: [200, 100, 200, 100, 200], // Vibration pattern
      tag: `raas-task-${task.id}`,
      requireInteraction: true, // Keep notification visible until user interacts
      silent: false,
      data: {
        taskId: task.id,
        url: '/'
      }
    };

    new Notification(`⚡ ${task.title}`, options);
  }

  // Show immediate notification for tasks due very soon (< 1 hour)
  showUrgentTasks(tasks) {
    if (this.permission !== 'granted') {
      return;
    }

    const now = new Date();
    const oneHourFromNow = new Date(now.getTime() + 60 * 60 * 1000);

    tasks.forEach(task => {
      if (task.completed) {
        return;
      }

      const dueDate = new Date(task.due_date);
      
      if (dueDate > now && dueDate <= oneHourFromNow) {
        this.showNotification(task);
      }
    });
  }
}

// Create global instance
window.raasNotifications = new RAASNotifications();

// Auto-initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.raasNotifications.init();
  });
} else {
  window.raasNotifications.init();
}
