// placement_project/static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    const signUpBtn = document.getElementById('signUpBtn');
    const signUpDropdown = document.getElementById('signUpDropdown');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    const newsletterForm = document.getElementById('newsletter-form');

    // Fetch CSRF token for newsletter form (only in index.html)
    if (newsletterForm) {
        fetch('/get-csrf-token/')
            .then(response => response.json())
            .then(data => {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = data.csrf_token;
                newsletterForm.appendChild(csrfInput);
            });
    }

    // Toggle signup dropdown visibility (only in index.html)
    if (signUpBtn && signUpDropdown) {
        signUpBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            signUpDropdown.classList.toggle('hidden');
        });

        // Close dropdown if user clicks outside of it
        document.addEventListener('click', (event) => {
            if (!signUpDropdown.contains(event.target) && !signUpBtn.contains(event.target)) {
                signUpDropdown.classList.add('hidden');
            }
        });
    }

    // Toggle mobile menu visibility (only in index.html)
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Intersection Observer for scroll animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.animate-on-scroll').forEach(element => {
        observer.observe(element);
    });

    // Smooth scrolling for anchor links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const targetId = event.currentTarget.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});