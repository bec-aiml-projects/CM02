// Import dependencies
const progressBars = {
    // Update progress bars
    updateProgressBars: function() {
        // Get progress bar elements
        const progressBarsElements = document.querySelectorAll(".progress-bar");
        // Update progress bar values
        progressBarsElements.forEach((progressBar) => {
            const progressBarValue = progressBar.querySelector("progress").value;
            progressBar.querySelector("label").textContent = `${progressBarValue}%`;
        });
    }
};