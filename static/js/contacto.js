/**
 * contacto.js - Junta Distrital de Villa Cutupú
 * Versión Profesional 1.0
 * Estilo consistente con main.js
 */

(function () {
    'use strict';

    // ===================================================
    // DOM ELEMENTOS
    // ===================================================
    const header   = document.querySelector('.main-header');
    const form     = document.getElementById('contactoForm');
    const body     = document.body;

    // ===================================================
    // UTILIDADES
    // ===================================================
    function throttle(func, limit) {
        let inThrottle;
        return function () {
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
    // 1. HEADER — OCULTAR AL BAJAR, MOSTRAR AL SUBIR
    // ===================================================
    if (header) {
        let lastScrollTop = 0;

        function handleHeaderScroll() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            // Sombra al hacer scroll
            if (scrollTop > 30) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }

            // Ocultar al bajar, mostrar al subir
            if (scrollTop > lastScrollTop && scrollTop > header.offsetHeight) {
                header.classList.add('header-hidden');
            } else {
                header.classList.remove('header-hidden');
            }

            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        }

        window.addEventListener('scroll', throttle(handleHeaderScroll, 100), { passive: true });
    }

    // ===================================================
    // 2. VALIDACIÓN DE FORMULARIO EN TIEMPO REAL
    // ===================================================
    if (form) {
        const requiredFields = form.querySelectorAll('[required]');

        function setError(input, msg) {
            input.style.borderColor = '#c0392b';
            input.style.boxShadow = '0 0 0 3px rgba(192,57,43,0.1)';
            let err = input.parentNode.querySelector('.field-error');
            if (!err) {
                err = document.createElement('span');
                err.className = 'field-error';
                err.style.cssText = 'font-size:0.75rem;color:#c0392b;font-weight:600;margin-top:3px;display:block;';
                input.parentNode.appendChild(err);
            }
            err.textContent = msg;
        }

        function clearError(input) {
            input.style.borderColor = '';
            input.style.boxShadow = '';
            const err = input.parentNode.querySelector('.field-error');
            if (err) err.remove();
        }

        function validateField(input) {
            if (!input.value.trim()) {
                setError(input, 'Este campo es requerido.');
                return false;
            }
            if (input.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value)) {
                setError(input, 'Ingrese un correo electrónico válido.');
                return false;
            }
            clearError(input);
            return true;
        }

        // Validación live al salir del campo
        requiredFields.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                if (input.value.trim()) clearError(input);
            });
        });

        // Validación al enviar
        form.addEventListener('submit', function (e) {
            let hasError = false;

            requiredFields.forEach(input => {
                if (!validateField(input)) hasError = true;
            });

            if (hasError) {
                e.preventDefault();
                // Scroll y foco al primer campo con error
                const firstInvalid = form.querySelector('.field-error');
                if (firstInvalid) {
                    const field = firstInvalid.closest('.form-group').querySelector('input, textarea');
                    field?.focus();
                    field?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }

    // ===================================================
    // 3. ANIMACIONES DE ENTRADA (Intersection Observer)
    // ===================================================
    const animTargets = document.querySelectorAll(
        '.contacto-info, .contacto-form, .mapa-container'
    );

    if (animTargets.length > 0) {
        animTargets.forEach((el, i) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(24px)';
            el.style.transition = `opacity 0.6s ease ${i * 0.1}s, transform 0.6s ease ${i * 0.1}s`;
        });

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animTargets.forEach(el => observer.observe(el));
    }

    // ===================================================
    // 4. DETECTAR DISPOSITIVOS TÁCTILES
    // ===================================================
    if ('ontouchstart' in window) {
        body.classList.add('touch-device');
    }

    // ===================================================
    // 5. PREVENIR CLICKS EN ENLACES VACÍOS
    // ===================================================
    document.querySelectorAll('a[href="#"]').forEach(link => {
        link.addEventListener('click', e => e.preventDefault());
    });

    // ===================================================
    // 6. MARCAR ENLACE ACTIVO SEGÚN LA URL
    // ===================================================
    const currentLocation = window.location.pathname;
    document.querySelectorAll('.main-nav a').forEach(item => {
        if (item.getAttribute('href') === currentLocation) {
            item.classList.add('active');
        }
    });

})();