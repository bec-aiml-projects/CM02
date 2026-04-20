// Import dependencies
const formHandler = {
    // Validate form data
    validateForm: function(formData) {
        // Get form fields
        const name = formData.get("name");
        const email = formData.get("email");
        const message = formData.get("message");
        // Validate form fields
        if (name === "" || email === "" || message === "") {
            return false;
        }
        return true;
    },
    // Handle form submission
    handleSubmit: function(event) {
        // Get form data
        const formData = new FormData(event.target);
        // Validate form data
        if (this.validateForm(formData)) {
            // Submit form data
            console.log("Form submitted successfully");
        } else {
            console.log("Form validation failed");
        }
    }
};