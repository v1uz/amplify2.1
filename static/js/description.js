document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const descriptionForm = document.getElementById('description-form');
    const urlInput = document.getElementById('url');
    const analyzeBtn = document.getElementById('analyze-btn');
    const btnText = analyzeBtn.querySelector('.btn-text');
    const spinner = analyzeBtn.querySelector('.spinner-border');
    const resultsSection = document.getElementById('results-section');
    const errorAlert = document.getElementById('error-alert');
    const companyTitle = document.getElementById('company-title');
    const metaDescription = document.getElementById('meta-description');
    const generatedDescription = document.getElementById('generated-description');
    const confidenceBadge = document.getElementById('confidence-badge');
    const copyBtn = document.getElementById('copy-btn');
    const regenerateBtn = document.getElementById('regenerate-btn');

    // Form submission handler
    descriptionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate URL
        const url = urlInput.value.trim();
        if (!isValidUrl(url)) {
            showError('Please enter a valid URL starting with http:// or https://');
            return;
        }
        
        // Show loading state
        setLoading(true);
        
        // Clear previous results
        hideError();
        
        // Make API request
        fetchDescription(url)
            .then(response => {
                // Show results
                displayResults(response);
                setLoading(false);
            })
            .catch(error => {
                showError('Error analyzing website: ' + error.message);
                setLoading(false);
            });
    });

    // Copy description button
    copyBtn.addEventListener('click', function() {
        const text = generatedDescription.textContent;
        navigator.clipboard.writeText(text)
            .then(() => {
                // Temporary feedback
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="bi bi-check-lg me-1"></i> Copied!';
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                }, 2000);
            })
            .catch(err => {
                showError('Failed to copy: ' + err.message);
            });
    });

    // Regenerate description
    regenerateBtn.addEventListener('click', function() {
        if (urlInput.value.trim()) {
            setLoading(true);
            fetchDescription(urlInput.value.trim(), true)
                .then(response => {
                    displayResults(response);
                    setLoading(false);
                })
                .catch(error => {
                    showError('Error regenerating description: ' + error.message);
                    setLoading(false);
                });
        }
    });

    // Helper functions
    function fetchDescription(url, regenerate = false) {
        return fetch('/api/description', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: url,
                regenerate: regenerate 
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        });
    }

    function displayResults(data) {
        // Update DOM with results
        companyTitle.textContent = data.title || 'Company';
        metaDescription.textContent = data.meta_description || 'No meta description found';
        generatedDescription.textContent = data.generated_description || 'Unable to generate description';
        
        // Update confidence score
        const confidence = data.confidence || 0;
        confidenceBadge.textContent = `Confidence: ${Math.round(confidence)}%`;
        
        // Show results section
        resultsSection.classList.remove('d-none');
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function setLoading(isLoading) {
        if (isLoading) {
            btnText.textContent = 'Analyzing...';
            spinner.classList.remove('d-none');
            analyzeBtn.disabled = true;
        } else {
            btnText.textContent = 'Analyze';
            spinner.classList.add('d-none');
            analyzeBtn.disabled = false;
        }
    }

    function showError(message) {
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
    }

    function hideError() {
        errorAlert.classList.add('d-none');
    }

    function isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (e) {
            return false;
        }
    }
});