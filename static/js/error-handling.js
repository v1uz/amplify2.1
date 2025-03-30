// Enhanced error handling for website input
const websiteInput = document.getElementById("websiteInput");
const continueBtn = document.getElementById("continueBtn");
const errorContainer = document.createElement("div");

// Style the error container
errorContainer.className = "error-container";
errorContainer.style.color = "red";
errorContainer.style.marginTop = "10px";
errorContainer.style.padding = "10px";
errorContainer.style.borderRadius = "5px";
errorContainer.style.display = "none";
errorContainer.style.animation = "fadeIn 0.3s";

// Add a CSS animation
const style = document.createElement("style");
style.textContent = `
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }
`;
document.head.appendChild(style);

// Add to DOM
websiteInput.parentElement.appendChild(errorContainer);

// Validate URL pattern
function isValidUrl(url) {
  // Basic URL validation regex - can be enhanced further
  const pattern = /^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
  return pattern.test(url);
}

// Input event handler with improved validation
websiteInput.addEventListener("input", function() {
  const value = this.value.trim();
  continueBtn.disabled = !value;
  continueBtn.style.backgroundColor = value ? "#1a1a1a" : "#B0B0B0";
  
  // Clear error when user starts typing again
  errorContainer.style.display = "none";
  websiteInput.style.borderColor = "#ccc";
});

// Enhanced click handler with validation
continueBtn.addEventListener("click", function() {
  let url = websiteInput.value.trim();
  
  if (!url) {
    displayError("Please enter a URL");
    return;
  }
  
  if (!isValidUrl(url)) {
    displayError("Please enter a valid URL (e.g., example.com or https://example.com)");
    return;
  }
  
  // Add protocol if missing
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url;
  }
  
  continueBtn.disabled = true;
  continueBtn.textContent = "Analyzing...";
  
  // Redirect to preloader with URL parameter
  window.location.href = `/preloader?url=${encodeURIComponent(url)}`;
});

// Function to display error messages
function displayError(message) {
  errorContainer.textContent = message;
  errorContainer.style.display = "block";
  
  // Shake the input to indicate error
  websiteInput.style.borderColor = "red";
  websiteInput.style.animation = "shake 0.5s";
  
  // Remove animation after it completes
  setTimeout(() => {
    websiteInput.style.animation = "";
  }, 500);
}