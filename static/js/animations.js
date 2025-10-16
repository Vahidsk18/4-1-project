// animations.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Initial Page Load Animations (Navbar, Sidebar) ---
    gsap.registerPlugin(ScrollTrigger); // Essential for scroll-triggered animations

    // Combined Navbar Brand (Logo and Text) animation
    gsap.from(".navbar-brand", {
        duration: 1.2,
        opacity: 0,
        x: -80,
        ease: "power3.out"
    });

    // Staggered animation for individual nav items in the header
    gsap.from(".navbar-nav .nav-item", {
        duration: 0.6,
        opacity: 0,
        y: -20,
        stagger: 0.1,
        ease: "back.out(1.7)",
        delay: 0.3
    });

    // Animate the sidebar on load (if visible)
    if (document.querySelector(".sidebar")) {
        gsap.from(".sidebar", {
            duration: 1,
            opacity: 0,
            x: -100,
            ease: "power2.out",
            delay: 0.7 // After navbar settles
        });
        // Staggered animation for sidebar nav links
        gsap.from(".sidebar .nav-link", {
            duration: 0.5,
            opacity: 0,
            x: -20,
            stagger: 0.08,
            ease: "power2.out",
            delay: 1 // After sidebar itself animates
        });
    }

    // Main content area fade-in (generalized for all pages)
    gsap.from(".main-content", {
        duration: 1,
        opacity: 0,
        y: 30,
        delay: 1.2,
        ease: "power2.out"
    });

    // Alert Messages Animation (more pronounced)
    gsap.from(".alert", {
        duration: 0.6,
        y: -50,
        opacity: 0,
        ease: "elastic.out(1, 0.7)", // Bouncy entrance
        delay: 0.5 // Appear shortly after page loads
    });

    // --- Dashboard Specific Animations ---

    // Dashboard Heading animation
    gsap.from(".dashboard-heading", {
        duration: 0.8,
        opacity: 0,
        y: -20,
        ease: "power2.out",
        delay: 1.5 // After main content animation starts
    });

    // Stat Cards animation (more dynamic entrance)
    gsap.utils.toArray(".stat-card-wrap").forEach(cardWrap => { // Target the wrapper for stagger
        const statCard = cardWrap.querySelector(".stat-card");
        const statValue = statCard.querySelector(".stat-value");
        const initialValue = parseInt(statValue.textContent) || 0; // Get current value

        gsap.from(statCard, {
            scrollTrigger: {
                trigger: cardWrap,
                start: "top 85%",
                end: "bottom 20%",
                toggleActions: "play none none reverse",
                // markers: true,
            },
            duration: 0.8,
            opacity: 0,
            y: 50,
            scale: 0.9,
            ease: "back.out(1.5)",
            onComplete: () => {
                // Animate the number count on reveal
                gsap.fromTo(statValue,
                    { innerHTML: 0 },
                    {
                        duration: 1,
                        innerHTML: initialValue,
                        snap: "innerHTML", // Snap to integer values
                        ease: "power1.out",
                    }
                );
            }
        });
    });

    // Table Header animation (applies to recent jobs/applications tables)
    gsap.utils.toArray(".table-dark").forEach(tableHead => {
        gsap.from(tableHead.querySelectorAll("th"), {
            scrollTrigger: {
                trigger: tableHead,
                start: "top 90%",
                toggleActions: "play none none none"
            },
            opacity: 0,
            y: -10,
            stagger: 0.1,
            duration: 0.5,
            ease: "power2.out"
        });
    });

    // Table rows within cards (already in base.js but good to confirm)
    gsap.utils.toArray(".table-responsive table tbody tr").forEach(row => {
        gsap.from(row, {
            scrollTrigger: {
                trigger: row,
                start: "top 95%",
                toggleActions: "play none none none"
            },
            opacity: 0,
            y: 20,
            duration: 0.4,
            ease: "power1.out"
        });
    });


    // --- General Interactive Animations (Hover Effects - via GSAP) ---
    // Enhanced Button Hover: Scale and subtle shadow change
    gsap.utils.toArray(".btn:not(.btn-close)").forEach(button => { // Exclude Bootstrap's close button
        gsap.to(button, {
            scale: 1,
            boxShadow: "0px 2px 4px rgba(0,0,0,0.08)", // Default shadow
            duration: 0.2,
            ease: "power2.out",
            paused: true,
            onHover: function() {
                gsap.to(button, {
                    scale: 1.05,
                    boxShadow: "0px 8px 20px rgba(0,0,0,0.3)",
                    duration: 0.2
                });
            },
            onLeave: function() {
                gsap.to(button, {
                    scale: 1,
                    boxShadow: "0px 2px 4px rgba(0,0,0,0.08)",
                    duration: 0.2
                });
            }
        });
    });

    // Card Hover Effect
    gsap.utils.toArray(".card.shadow-sm, .card.shadow-lg").forEach(card => {
        gsap.to(card, {
            y: 0,
            boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
            duration: 0.2,
            ease: "power1.out",
            paused: true,
            onHover: function() {
                gsap.to(card, {
                    y: -5,
                    boxShadow: "0 10px 20px rgba(0,0,0,0.2)",
                    duration: 0.2
                });
            },
            onLeave: function() {
                gsap.to(card, {
                    y: 0,
                    boxShadow: "0 4px 8px rgba(0,0,0,0.1)",
                    duration: 0.2
                });
            }
        });
    });
});