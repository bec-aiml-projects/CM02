// Import dependencies
// Initialize event listeners and dynamic effects
function init() {
    // Add event listener for form submission
    document.getElementById("contact-form").addEventListener("submit", function(event) {
        event.preventDefault();
        formHandler.handleSubmit(event);
    });
    // Update progress bars
    progressBars.updateProgressBars();
}

// Initialize application
init();
