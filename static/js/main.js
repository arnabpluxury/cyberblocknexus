// Main JavaScript file for HackBlockNexus

// Enable Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
});

// Flash message auto-dismiss
document.addEventListener('DOMContentLoaded', function() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    var forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

// CTF challenge submission
function submitFlag(challengeId) {
    const flagInput = document.querySelector(`#flag-${challengeId}`);
    const flag = flagInput.value;
    
    fetch('/ctf/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            challenge_id: challengeId,
            flag: flag
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Congratulations! Flag is correct!');
            updateScore(data.points);
        } else {
            showAlert('danger', 'Incorrect flag. Try again!');
        }
        flagInput.value = '';
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'An error occurred. Please try again.');
    });
}

// Show alert message
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

// Update user score
function updateScore(points) {
    const scoreElement = document.querySelector('#user-score');
    if (scoreElement) {
        const currentScore = parseInt(scoreElement.textContent);
        scoreElement.textContent = currentScore + points;
    }
}

// Event registration
function registerForEvent(eventId) {
    fetch('/events/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            event_id: eventId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Successfully registered for the event!');
            updateEventButton(eventId);
        } else {
            showAlert('danger', data.message || 'Registration failed. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'An error occurred. Please try again.');
    });
}

// Update event registration button
function updateEventButton(eventId) {
    const button = document.querySelector(`#register-${eventId}`);
    if (button) {
        button.textContent = 'Registered';
        button.disabled = true;
        button.classList.remove('btn-primary');
        button.classList.add('btn-success');
    }
}

// Dark mode toggle
const darkModeToggle = document.querySelector('#darkModeToggle');
if (darkModeToggle) {
    darkModeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
    });
    
    // Check for saved dark mode preference
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
}

// Profile image upload preview
const profileImageInput = document.querySelector('#profileImage');
if (profileImageInput) {
    profileImageInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = document.querySelector('#imagePreview');
                preview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });
}



document.addEventListener('DOMContentLoaded', function() {
    const terminalOutput = document.getElementById('typing-output');
    const demoContent = [
        {
            description: "// Initializing the CTF challenge environment...",
            code: "from flask import Flask, render_template\napp = Flask(__name__)"
        },
        {
            description: "// Setting up database connection...",
            code: "import sqlite3\ndb = sqlite3.connect('challenges.db')"
        },
        {
            description: "// Loading encryption module...",
            code: "from cryptography.fernet import Fernet\nkey = Fernet.generate_key()"
        },
        {
            description: "// Starting web server...",
            code: "if __name__ == '__main__':\n    app.run(debug=True)"
        }
    ];

    let currentItem = 0;
    let currentChar = 0;
    let isTyping = false;
    let currentLine = null;

    function typeText() {
        if (currentItem >= demoContent.length) {
            // Animation complete
            addCursor(false);
            return;
        }

        const item = demoContent[currentItem];
        
        if (!isTyping) {
            // Create new line for description
            currentLine = document.createElement('div');
            currentLine.className = 'terminal-line';
            terminalOutput.appendChild(currentLine);
            isTyping = true;
            currentChar = 0;
            typeNextCharacter(item.description, 'comment', () => {
                // Description typing complete
                setTimeout(() => {
                    // Create new line for code
                    currentLine = document.createElement('div');
                    currentLine.className = 'terminal-line';
                    terminalOutput.appendChild(currentLine);
                    currentChar = 0;
                    typeNextCharacter(item.code, 'code', () => {
                        // Code typing complete
                        isTyping = false;
                        currentItem++;
                        setTimeout(typeText, 500);
                    });
                }, 300);
            });
        }
    }

    function typeNextCharacter(text, className, callback) {
        if (currentChar < text.length) {
            addCursor(true);
            setTimeout(() => {
                currentLine.innerHTML = text.substring(0, currentChar + 1) + 
                                      `<span class="${className}"></span>`;
                currentChar++;
                typeNextCharacter(text, className, callback);
            }, Math.random() * 50 + 30); // Random typing speed
        } else {
            addCursor(false);
            currentLine.querySelector(`.${className}`).textContent = 
                text.substring(0, currentChar);
            if (callback) callback();
        }
    }

    function addCursor(show) {
        const cursor = document.querySelector('.typing-cursor');
        if (cursor) cursor.remove();
        
        if (show) {
            const cursor = document.createElement('span');
            cursor.className = 'typing-cursor';
            currentLine.appendChild(cursor);
        }
    }

    // Start the animation after a short delay
    setTimeout(typeText, 1000);
});