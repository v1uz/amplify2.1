document.addEventListener("DOMContentLoaded", () => {
    console.log("Page Loaded Successfully");

    const tryBtn = document.getElementById("tryNowBtn");
    const learnBtn = document.getElementById("learnMoreBtn");

    if (tryBtn) {
        tryBtn.addEventListener("click", () => {
            console.log("Try It Right Now button clicked");
            window.location.href = "/amplify"; // Redirect to amplify page
        });
    }

    if (learnBtn) {
        learnBtn.addEventListener("click", () => {
            console.log("Learn More button clicked");
            window.location.href = "/amplify"; // Redirect to amplify page
        });
    }
});