const websiteInput = document.getElementById("websiteInput");
const continueBtn = document.getElementById("continueBtn");
const domainInput = document.getElementById("domain");
const descriptionInput = document.getElementById("description");
const keywordsInput = document.getElementById("keywords");
const promptInput = document.getElementById("prompt");
const errorMessage = document.createElement("p");
websiteInput.parentElement.appendChild(errorMessage);

websiteInput.addEventListener("input", function() {
    continueBtn.disabled = !this.value.trim();
    continueBtn.style.backgroundColor = this.value.trim() ? "#1a1a1a" : "#B0B0B0";
    errorMessage.style.display = "none";
});

continueBtn.addEventListener("click", function() {
    let url = websiteInput.value.trim();
    if (!url) {
        errorMessage.textContent = "Пожалуйста, введите URL.";
        errorMessage.style.display = "block";
        return;
    }

    continueBtn.disabled = true;
    continueBtn.textContent = "Анализ...";
    errorMessage.style.display = "none";

    // Redirect to preloader with URL parameter
    window.location.href = `/preloader?url=${encodeURIComponent(url)}`;
});