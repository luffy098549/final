/**
 * servicios.js — Junta Distrital de Villa Cutupú
 * Compatible con la estructura premium de cards (card-header / service-card-footer)
 */

(function () {
    'use strict';

    // ── Utilidad: throttle ──────────────────────────────
    function throttle(fn, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                fn.apply(this, args);
                inThrottle = true;
                setTimeout(() => (inThrottle = false), limit);
            }
        };
    }

    // ===================================================
    // 1. FILTROS
    // ===================================================
    const filtros  = document.querySelectorAll('.filtro-btn');
    const cards    = document.querySelectorAll('.service-card');
    const contador = document.getElementById('contador');

    function filtrarServicios(filtro) {
        let visibles = 0;

        cards.forEach((card, i) => {
            const tipo    = card.dataset.tipo;
            const mostrar = filtro === 'todos' || tipo === filtro;

            if (mostrar) {
                card.classList.remove('hidden');
                // Re-disparar animación escalonada
                card.style.animation = 'none';
                void card.offsetHeight; // reflow
                card.style.animation = '';
                card.style.animationDelay = `${i * 0.04}s`;
                visibles++;
            } else {
                card.classList.add('hidden');
            }
        });

        if (contador) contador.textContent = visibles;

        filtros.forEach(btn =>
            btn.classList.toggle('active', btn.dataset.filtro === filtro)
        );
    }

    filtros.forEach(btn =>
        btn.addEventListener('click', function () {
            filtrarServicios(this.dataset.filtro);
        })
    );

    // Inicializar contador real
    if (contador) contador.textContent = cards.length;

    // ===================================================
    // 2. ANIMACIÓN DE ENTRADA (IntersectionObserver)
    //    Solo actúa sobre cards fuera del viewport inicial
    // ===================================================
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity    = '1';
                        entry.target.style.transform  = 'translateY(0)';
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
        );

        // Solo observar cards que empiezan fuera de la vista
        cards.forEach((card) => {
            const rect = card.getBoundingClientRect();
            if (rect.top > window.innerHeight) {
                card.style.opacity   = '0';
                card.style.transform = 'translateY(24px)';
                card.style.transition = 'opacity 0.55s ease, transform 0.55s ease';
                observer.observe(card);
            }
        });
    }

    // ===================================================
    // 3. BÚSQUEDA (opcional — activa si existe #searchServicios)
    // ===================================================
    const searchInput = document.getElementById('searchServicios');
    if (searchInput) {
        searchInput.addEventListener('input', throttle(function () {
            const term = this.value.toLowerCase().trim();

            let visibles = 0;
            cards.forEach((card) => {
                const titulo = card.querySelector('h3')?.textContent.toLowerCase() ?? '';
                const desc   = card.querySelector('p')?.textContent.toLowerCase()  ?? '';
                const match  = titulo.includes(term) || desc.includes(term);

                card.classList.toggle('hidden', !match);
                if (match) visibles++;
            });

            if (contador) contador.textContent = visibles;
        }, 250));
    }

    // ===================================================
    // 4. FEEDBACK VISUAL AL HACER CLIC EN BOTÓN DE SERVICIO
    // ===================================================
    document.querySelectorAll('.btn-servicio').forEach((btn) => {
        btn.addEventListener('click', function () {
            this.style.opacity        = '0.65';
            this.style.pointerEvents  = 'none';
        });
    });

    // ===================================================
    // 5. HEADER: scrolled + hide-on-scroll-down
    // ===================================================
    const header = document.querySelector('.main-header');
    if (header) {
        let lastScroll = 0;

        window.addEventListener('scroll', throttle(() => {
            const current = window.scrollY;

            header.classList.toggle('scrolled', current > 50);

            if (current > lastScroll && current > 200) {
                header.classList.add('header-hidden');
            } else {
                header.classList.remove('header-hidden');
            }

            lastScroll = current;
        }, 100));
    }

    // ===================================================
    // 6. BOTÓN VOLVER ARRIBA
    // ===================================================
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', throttle(() => {
            backToTop.classList.toggle('visible', window.scrollY > 300);
        }, 100));

        backToTop.addEventListener('click', () =>
            window.scrollTo({ top: 0, behavior: 'smooth' })
        );
    }

    // ===================================================
    // 7. PREVENIR href="#" vacíos
    // ===================================================
    document.querySelectorAll('a[href="#"]').forEach((a) =>
        a.addEventListener('click', (e) => e.preventDefault())
    );

})();