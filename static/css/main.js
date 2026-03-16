// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
    
    // Password strength indicator
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            updatePasswordStrengthIndicator(strength);
        });
    }
});

function checkPasswordStrength(password) {
    let score = 0;
    
    // Length check
    if (password.length >= 12) score += 1;
    if (password.length >= 16) score += 1;
    
    // Character type checks
    if (/[A-Z]/.test(password)) score += 1;
    if (/[a-z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    
    // Avoid common patterns
    if (!/(password|123456|qwerty|admin)/i.test(password)) score += 1;
    
    return score;
}

function updatePasswordStrengthIndicator(score) {
    let indicator = document.querySelector('.password-strength');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'password-strength';
        const passwordGroup = document.querySelector('.form-group #password').parentNode;
        passwordGroup.appendChild(indicator);
    }
    
    const strengthText = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
    const strengthColor = ['#e74c3c', '#e67e22', '#f1c40f', '#3498db', '#2ecc71', '#27ae60'];
    
    indicator.textContent = `Strength: ${strengthText[score]}`;
    indicator.style.color = strengthColor[score];
    indicator.style.marginTop = '0.5rem';
    indicator.style.fontWeight = 'bold';
}
