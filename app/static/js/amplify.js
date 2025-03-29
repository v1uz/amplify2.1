const websiteInput = document.getElementById("websiteInput");
const continueBtn = document.getElementById("continueBtn");
const errorMessage = document.createElement("p");

// Set up error message styling
errorMessage.classList.add("error-message");
errorMessage.style.display = "none";
websiteInput.parentElement.appendChild(errorMessage);

// Input validation
websiteInput.addEventListener("input", function() {
    const hasValue = this.value.trim();
    continueBtn.disabled = !hasValue;
    continueBtn.classList.toggle("btn-disabled", !hasValue);
    continueBtn.classList.toggle("btn-active", hasValue);
    errorMessage.style.display = "none";
});

// URL validation helper
function isValidURL(url) {
    try {
        // Add protocol if missing
        if (!/^https?:\/\//i.test(url)) {
            url = 'https://' + url;
        }
        new URL(url);
        return true;
    } catch (e) {
        return false;
    }
}

// Handle form submission
continueBtn.addEventListener("click", function() {
    let url = websiteInput.value.trim();
    
    // Validate input
    if (!url) {
        errorMessage.textContent = "Пожалуйста, введите URL.";
        errorMessage.style.display = "block";
        return;
    }
    
    // Validate URL format
    if (!isValidURL(url)) {
        errorMessage.textContent = "Пожалуйста, введите корректный URL.";
        errorMessage.style.display = "block";
        return;
    }
    
    // Update button state
    continueBtn.disabled = true;
    continueBtn.textContent = "Анализ...";
    continueBtn.classList.add("btn-loading");
    errorMessage.style.display = "none";
    
    // Add protocol if missing
    if (!/^https?:\/\//i.test(url)) {
        url = 'https://' + url;
    }
    
    // Redirect to preloader with URL parameter
    window.location.href = `/preloader?url=${encodeURIComponent(url)}`;
});

// Allow form submission with Enter key
websiteInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter" && !continueBtn.disabled) {
        continueBtn.click();
    }
});