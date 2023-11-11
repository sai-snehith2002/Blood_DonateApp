$(document).ready(function() {
    // Add any jQuery functionality you need here

    // Initialize ReCaptcha
    grecaptcha.ready(function() {
        grecaptcha.execute('YOUR_RECAPTCHA_SITE_KEY', {action: 'registration'}).then(function(token) {
            // Add the token to your registration form
            document.getElementById('g-recaptcha-response').value = token;
        });
    });
});
