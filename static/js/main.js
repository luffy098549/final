/**
 * main.js - Junta Distrital de Villa Cutupú
 * Versión Profesional 9.9/10
 * Optimizado para rendimiento, accesibilidad y mantenibilidad
 */

(function() {
    'use strict';

    // ===================================================
    // DOM ELEMENTOS PRINCIPALES
    // ===================================================
    const header = document.querySelector('.main-header');
    const menuToggle = document.getElementById('menuToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('overlay');
    const backToTop = document.getElementById('backToTop');
    const body = document.body;

    // ===================================================
    // UTILIDADES (throttle para scroll)
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
    // 1. HEADER HIDE ON SCROLL (ocultar al bajar, mostrar al subir)
    // ===================================================
    if (header) {
        let lastScrollTop = 0;
        const headerHeight = header.offsetHeight;
        const scrollThreshold = 50;

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
    // 2. MENÚ MÓVIL (hamburguesa)
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
            if (mobileMenu.classList.contains('active')) {
                closeMobileMenu();
            } else {
                openMobileMenu();
            }
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
    // 3. ANIMACIONES AL HACER SCROLL (Intersection Observer)
    //    EXCLUYE IMÁGENES Y GALERÍA
    // ===================================================
    const animatedElements = document.querySelectorAll(
        '.accion-card, .autoridad-card, .vocal-card, .mensaje-contenido'
    );

    if (animatedElements.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2, rootMargin: '0px 0px -50px 0px' });

        animatedElements.forEach(el => observer.observe(el));
    }

    // ===================================================
    // 4. GALERÍA - MODAL (lightbox) - SIN ANIMACIÓN DE ENTRADA
    // ===================================================
    const galleryItems = document.querySelectorAll('.galeria-item');
    const modal = document.querySelector('.image-modal');

    if (galleryItems.length > 0 && modal) {
        const modalImg = modal.querySelector('.modal-image');
        const modalCaption = modal.querySelector('.modal-caption');
        const modalClose = modal.querySelector('.modal-close');
        const modalPrev = modal.querySelector('.modal-prev');
        const modalNext = modal.querySelector('.modal-next');

        let currentIndex = 0;
        const images = Array.from(galleryItems).map(item => ({
            src: item.querySelector('img').src,
            caption: item.querySelector('.galeria-caption')?.textContent || ''
        }));

        function openModal(index) {
            if (index < 0 || index >= images.length) return;
            currentIndex = index;
            modalImg.src = images[currentIndex].src;
            modalCaption.textContent = images[currentIndex].caption;
            modal.classList.add('active');
            body.style.overflow = 'hidden';
        }

        function closeModal() {
            modal.classList.remove('active');
            body.style.overflow = '';
        }

        function prevImage() {
            currentIndex = (currentIndex - 1 + images.length) % images.length;
            openModal(currentIndex);
        }

        function nextImage() {
            currentIndex = (currentIndex + 1) % images.length;
            openModal(currentIndex);
        }

        galleryItems.forEach((item, index) => {
            item.addEventListener('click', () => openModal(index));
        });

        if (modalClose) modalClose.addEventListener('click', closeModal);
        if (modalPrev) modalPrev.addEventListener('click', prevImage);
        if (modalNext) modalNext.addEventListener('click', nextImage);

        document.addEventListener('keydown', (e) => {
            if (!modal.classList.contains('active')) return;
            switch (e.key) {
                case 'Escape': closeModal(); break;
                case 'ArrowLeft': prevImage(); break;
                case 'ArrowRight': nextImage(); break;
            }
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    }

    // ===================================================
    // 5. BOTÓN VOLVER ARRIBA
    // ===================================================
    if (backToTop) {
        function toggleBackToTop() {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        }

        window.addEventListener('scroll', throttle(toggleBackToTop, 100));
        toggleBackToTop();

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
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                if (mobileMenu && mobileMenu.classList.contains('active')) {
                    closeMobileMenu?.();
                }
            }
        });
    });

    // ===================================================
    // 7. DETECTAR DISPOSITIVOS TÁCTILES
    // ===================================================
    if ('ontouchstart' in window) {
        body.classList.add('touch-device');
    }

    // ===================================================
    // 8. PREVENIR CLICKS EN ENLACES VACÍOS
    // ===================================================
    document.querySelectorAll('a[href="#"]').forEach(link => {
        link.addEventListener('click', (e) => e.preventDefault());
    });

    // ===================================================
    // 9. CARGA INICIAL (animar elementos ya visibles)
    //    EXCLUYE IMÁGENES Y GALERÍA
    // ===================================================
    setTimeout(() => {
        animatedElements.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.top < window.innerHeight - 100 && rect.bottom > 0) {
                el.classList.add('fade-in-up');
            }
        });
    }, 200);

    // ===================================================
    // 10. MARCAR ENLACE ACTIVO SEGÚN LA URL
    // ===================================================
    const currentLocation = window.location.pathname;
    const menuItems = document.querySelectorAll('.main-nav a, .mobile-menu a');
    menuItems.forEach(item => {
        if (item.getAttribute('href') === currentLocation) {
            item.classList.add('active');
        }
    });

})();