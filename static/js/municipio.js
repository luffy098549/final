/**
 * municipio.js - Junta Distrital de Villa Cutupú
 * Adaptado desde main.js
 */

(function() {
    'use strict';

    const header     = document.querySelector('.main-header');
    const menuToggle = document.getElementById('menuToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    const overlay    = document.getElementById('overlay');
    const backToTop  = document.getElementById('backToTop');
    const body       = document.body;

    // ===================================================
    // THROTTLE
    // ===================================================
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments, context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ===================================================
    // 1. HEADER SCROLL + sincronizar page-nav
    // ===================================================
    const pageNav = document.querySelector('.page-nav');

    if (header) {
        let lastScrollTop = 0;
        const headerHeight = header.offsetHeight;

        function handleHeaderScroll() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            header.classList.toggle('scrolled', scrollTop > 30);

            if (scrollTop > lastScrollTop && scrollTop > headerHeight) {
                header.classList.add('header-hidden');
                if (pageNav) pageNav.style.top = '0px';
            } else {
                header.classList.remove('header-hidden');
                if (pageNav) pageNav.style.top = headerHeight + 'px';
            }
            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        }

        // Inicializar top del nav
        if (pageNav) pageNav.style.top = headerHeight + 'px';

        window.addEventListener('scroll', throttle(handleHeaderScroll, 100));
    }

    // ===================================================
    // 2. MENÚ MÓVIL
    // ===================================================
    if (menuToggle && mobileMenu && overlay) {
        function openMobileMenu() {
            menuToggle.classList.add('active');
            mobileMenu.classList.add('active');
            overlay.classList.add('active');
            body.classList.add('menu-open');
            menuToggle.setAttribute('aria-expanded', 'true');
        }

        function closeMobileMenu() {
            menuToggle.classList.remove('active');
            mobileMenu.classList.remove('active');
            overlay.classList.remove('active');
            body.classList.remove('menu-open');
            menuToggle.setAttribute('aria-expanded', 'false');
        }

        menuToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            mobileMenu.classList.contains('active') ? closeMobileMenu() : openMobileMenu();
        });

        overlay.addEventListener('click', closeMobileMenu);
        mobileMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMobileMenu));
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && mobileMenu.classList.contains('active')) closeMobileMenu();
        });
    }

    // ===================================================
    // 3. ANIMACIONES AL HACER SCROLL
    // ===================================================
    const animatedElements = document.querySelectorAll(
        '.page h2, .page h3, .page ul:not(.services) li, .services li'
    );

    if (animatedElements.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });

        animatedElements.forEach(el => observer.observe(el));
    }

    // ===================================================
    // 4. NAVEGACIÓN INTERNA ACTIVA AL HACER SCROLL
    //    (resalta el link del .page-nav según sección visible)
    // ===================================================
    const pageNavLinks = document.querySelectorAll('.page-nav a[href^="#"]');
    const sections = Array.from(pageNavLinks).map(link => {
        const id = link.getAttribute('href').slice(1);
        return document.getElementById(id);
    }).filter(Boolean);

    if (sections.length > 0 && pageNavLinks.length > 0) {
        function updateActiveNavLink() {
            const scrollPos = window.scrollY + 200;
            let current = sections[0];

            sections.forEach(section => {
                if (section.offsetTop <= scrollPos) current = section;
            });

            pageNavLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current.id) {
                    link.classList.add('active');
                }
            });
        }

        window.addEventListener('scroll', throttle(updateActiveNavLink, 100));
        updateActiveNavLink();
    }

    // ===================================================
    // 5. BOTÓN VOLVER ARRIBA
    // ===================================================
    if (backToTop) {
        window.addEventListener('scroll', throttle(() => {
            backToTop.classList.toggle('visible', window.scrollY > 300);
        }, 100));

        backToTop.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ===================================================
    // 6. SCROLL SUAVE PARA ENLACES INTERNOS
    // ===================================================
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ===================================================
    // 7. TOUCH / TÁCTIL
    // ===================================================
    if ('ontouchstart' in window) body.classList.add('touch-device');

    // ===================================================
    // 8. MARCAR ENLACE ACTIVO EN NAV PRINCIPAL
    // ===================================================
    const currentLocation = window.location.pathname;
    document.querySelectorAll('.main-nav a, .mobile-menu a').forEach(item => {
        if (item.getAttribute('href') === currentLocation) item.classList.add('active');
    });

    // ===================================================
    // 9. PREVENIR CLICKS EN ENLACES VACÍOS
    // ===================================================
    document.querySelectorAll('a[href="#"]').forEach(link => {
        link.addEventListener('click', (e) => e.preventDefault());
    });

    // ===================================================
    // 10. CARGA INICIAL — animar elementos ya visibles
    // ===================================================
    setTimeout(() => {
        animatedElements.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.top < window.innerHeight - 80 && rect.bottom > 0) {
                el.classList.add('fade-in-up');
            }
        });
    }, 200);

})();