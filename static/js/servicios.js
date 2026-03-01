/**
 * servicios.js - Junta Distrital de Villa Cutupú
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
    // 1. HEADER SCROLL
    // ===================================================
    if (header) {
        let lastScrollTop = 0;
        const headerHeight = header.offsetHeight;

        function handleHeaderScroll() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            header.classList.toggle('scrolled', scrollTop > 30);
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
        mobileMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMobileMenu));
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && mobileMenu.classList.contains('active')) closeMobileMenu();
        });
    }

    // ===================================================
    // 3. FILTROS DE CATEGORÍA
    // ===================================================
    const filtros   = document.querySelectorAll('.filtro-btn');
    const cards     = document.querySelectorAll('.service-card');
    const contador  = document.getElementById('contador');

    filtros.forEach(btn => {
        btn.addEventListener('click', () => {
            // Actualizar botón activo
            filtros.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filtro = btn.dataset.filtro;
            let visibles = 0;

            cards.forEach(card => {
                const tipo = card.dataset.tipo;
                const mostrar = filtro === 'todos' || tipo === filtro;

                if (mostrar) {
                    card.style.display = '';
                    // Reanimar
                    card.classList.remove('fade-in-up');
                    void card.offsetWidth; // reflow
                    card.classList.add('fade-in-up');
                    visibles++;
                } else {
                    card.style.display = 'none';
                }
            });

            if (contador) contador.textContent = visibles;
        });
    });

    // ===================================================
    // 4. ANIMACIONES AL HACER SCROLL
    // ===================================================
    if (cards.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });

        cards.forEach(card => observer.observe(card));
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
    // 6. TOUCH / TÁCTIL
    // ===================================================
    if ('ontouchstart' in window) body.classList.add('touch-device');

    // ===================================================
    // 7. MARCAR ENLACE ACTIVO
    // ===================================================
    const currentLocation = window.location.pathname;
    document.querySelectorAll('.main-nav a, .mobile-menu a').forEach(item => {
        if (item.getAttribute('href') === currentLocation) item.classList.add('active');
    });

    // ===================================================
    // 8. PREVENIR CLICKS EN ENLACES VACÍOS
    // ===================================================
    document.querySelectorAll('a[href="#"]').forEach(link => {
        link.addEventListener('click', (e) => e.preventDefault());
    });

    // ===================================================
    // 9. CARGA INICIAL
    // ===================================================
    setTimeout(() => {
        cards.forEach(card => {
            const rect = card.getBoundingClientRect();
            if (rect.top < window.innerHeight - 80 && rect.bottom > 0) {
                card.classList.add('fade-in-up');
            }
        });
    }, 200);

})();