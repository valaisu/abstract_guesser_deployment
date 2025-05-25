// Main JavaScript file for the website

document.addEventListener('DOMContentLoaded', () => {
    // Initialize any global UI components
    initializeUI();
    
    // Add event listeners
    setupEventListeners();
});

function initializeUI() {
    // Add any global UI initialization here
    console.log('Website initialized');
    
    // Flash message auto-hide
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
            }, 500);
        }, 3000);
    });
}

function setupEventListeners() {
    // Add any global event listeners here
    
    // Example: Close flash messages when clicked
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(message => {
        message.addEventListener('click', () => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
            }, 500);
        });
    });
}
