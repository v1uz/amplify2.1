// Optional: Add a back button functionality
document.addEventListener('DOMContentLoaded', function() {
    const backButton = document.createElement('button');
    backButton.textContent = 'Вернуться на главную';
    backButton.style.padding = '10px 20px';
    backButton.style.backgroundColor = '#1a1a1a';
    backButton.style.color = 'white';
    backButton.style.border = 'none';
    backButton.style.borderRadius = '5px';
    backButton.style.cursor = 'pointer';
    backButton.style.marginTop = '20px';

    backButton.addEventListener('click', function() {
        window.location.href = '/';
    });

    document.querySelector('.result-section').appendChild(backButton);
});