/**
 * login.js - Junta Distrital de Villa Cutupú
 * Adaptado desde main.js
 */

(function() {
    'use strict';

    const header = document.querySelector('.main-header');
    const menuToggle = document.getElementById('menuToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('overlay');
    const body = document.body;

    // ===================================================
    // THROTTLE
    // ===================================================
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ===================================================
    // 1. HEADER SCROLL
    // ===================================================
    if (header) {
        let lastScrollTop = 0;
        const headerHeight = header.offsetHeight;

        function handleHeaderScroll() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            if (scrollTop > 30) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }

            if (scrollTop > lastScrollTop && scrollTop > headerHeight) {
                header.classList.add('header-hidden');
            } else {
                header.classList.remove('header-hidden');
            }

            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        }

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

        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMobileMenu);
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
                closeMobileMenu();
            }
        });
    }

    // ===================================================
    // 3. DETECTAR DISPOSITIVOS TÁCTILES
    // ===================================================
    if ('ontouchstart' in window) {
        body.classList.add('touch-device');
    }

    // ===================================================
    // 4. MARCAR ENLACE ACTIVO
    // ===================================================
    const currentLocation = window.location.pathname;
    document.querySelectorAll('.main-nav a, .mobile-menu a').forEach(item => {
        if (item.getAttribute('href') === currentLocation) {
            item.classList.add('active');
        }
    });

    // ===================================================
    // 5. PREVENIR CLICKS EN ENLACES VACÍOS
    // ===================================================
    document.querySelectorAll('a[href="#"]').forEach(link => {
        link.addEventListener('click', (e) => e.preventDefault());
    });

})();