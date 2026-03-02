/**
 * noticias-likes.js - Junta Distrital de Villa Cutupú
 * Sistema de Likes para tarjetas de noticias
 * Versión 1.0 — Estilo consistente con main.js
 */

(function () {
    'use strict';

    // ===================================================
    // CONFIGURACIÓN
    // ===================================================
    const STORAGE_KEY = 'cutupu_likes';
    const LIKE_ANIMATION_DURATION = 300; // ms

    // ===================================================
    // UTILIDADES
    // ===================================================

    /**
     * Lee todos los likes guardados en localStorage.
     * @returns {Object} Mapa { slug: count }
     */
    function getLikesData() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        } catch (e) {
            return {};
        }
    }

    /**
     * Persiste el objeto de likes en localStorage.
     * @param {Object} data
     */
    function saveLikesData(data) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        } catch (e) {
            console.warn('[Likes] No se pudo guardar en localStorage:', e);
        }
    }

    /**
     * Lee qué noticias ya likeo el usuario en esta sesión/dispositivo.
     * @returns {Set<string>}
     */
    function getLikedByUser() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY + '_user');
            return new Set(JSON.parse(raw) || []);
        } catch (e) {
            return new Set();
        }
    }

    /**
     * Persiste el set de noticias likeadas por el usuario.
     * @param {Set<string>} set
     */
    function saveLikedByUser(set) {
        try {
            localStorage.setItem(STORAGE_KEY + '_user', JSON.stringify([...set]));
        } catch (e) {
            console.warn('[Likes] No se pudo guardar preferencias del usuario:', e);
        }
    }

    // ===================================================
    // 1. INYECTAR BOTÓN DE LIKE EN CADA TARJETA
    // ===================================================
    function buildLikeButton(slug, count, alreadyLiked) {
        const btn = document.createElement('button');
        btn.className = 'like-btn' + (alreadyLiked ? ' like-btn--active' : '');
        btn.setAttribute('aria-label', alreadyLiked ? 'Ya diste like' : 'Me gusta');
        btn.setAttribute('aria-pressed', alreadyLiked ? 'true' : 'false');
        btn.dataset.slug = slug;

        btn.innerHTML = `
            <span class="like-btn__icon" aria-hidden="true">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${alreadyLiked ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
            </span>
            <span class="like-btn__count">${count}</span>
        `;

        return btn;
    }

    function injectLikeButtons() {
        const cards = document.querySelectorAll('.noticia-card');
        if (!cards.length) return;

        const likesData  = getLikesData();
        const likedByUser = getLikedByUser();

        cards.forEach(card => {
            // Extraer slug desde el href del botón "Leer más"
            const readMore = card.querySelector('a.btn[href]');
            if (!readMore) return;

            const href = readMore.getAttribute('href'); // ej: /noticias/cierre-temporal-via
            const slug = href.split('/').filter(Boolean).pop(); // "cierre-temporal-via"
            if (!slug) return;

            const count       = likesData[slug] || 0;
            const alreadyLiked = likedByUser.has(slug);
            const btn         = buildLikeButton(slug, count, alreadyLiked);

            // Insertar después del botón "Leer más"
            readMore.parentNode.insertBefore(btn, readMore.nextSibling);
        });
    }

    // ===================================================
    // 2. LÓGICA DE LIKE / UNLIKE
    // ===================================================
    function handleLikeClick(e) {
        const btn = e.target.closest('.like-btn');
        if (!btn) return;

        const slug        = btn.dataset.slug;
        const likesData   = getLikesData();
        const likedByUser = getLikedByUser();
        const countEl     = btn.querySelector('.like-btn__count');
        const svgPath     = btn.querySelector('svg path');
        const isLiked     = likedByUser.has(slug);

        // Evitar doble clic durante animación
        if (btn.classList.contains('like-btn--animating')) return;

        // Actualizar estado
        if (isLiked) {
            // Unlike
            likedByUser.delete(slug);
            likesData[slug] = Math.max(0, (likesData[slug] || 1) - 1);
            btn.classList.remove('like-btn--active');
            btn.setAttribute('aria-pressed', 'false');
            btn.setAttribute('aria-label', 'Me gusta');
            if (svgPath) svgPath.setAttribute('fill', 'none');
        } else {
            // Like
            likedByUser.add(slug);
            likesData[slug] = (likesData[slug] || 0) + 1;
            btn.classList.add('like-btn--active');
            btn.setAttribute('aria-pressed', 'true');
            btn.setAttribute('aria-label', 'Ya diste like');
            if (svgPath) svgPath.setAttribute('fill', 'currentColor');

            // Animación de pulso
            triggerLikeAnimation(btn);
        }

        // Actualizar contador en pantalla
        if (countEl) countEl.textContent = likesData[slug];

        // Persistir
        saveLikesData(likesData);
        saveLikedByUser(likedByUser);
    }

    // ===================================================
    // 3. ANIMACIÓN DE LIKE
    // ===================================================
    function triggerLikeAnimation(btn) {
        btn.classList.add('like-btn--animating');

        // Partícula flotante
        spawnHeartParticle(btn);

        setTimeout(() => {
            btn.classList.remove('like-btn--animating');
        }, LIKE_ANIMATION_DURATION);
    }

    function spawnHeartParticle(btn) {
        const particle = document.createElement('span');
        particle.className = 'like-particle';
        particle.setAttribute('aria-hidden', 'true');
        particle.textContent = '♥';

        // Posicionar encima del botón
        const rect = btn.getBoundingClientRect();
        particle.style.left = (rect.left + rect.width / 2) + 'px';
        particle.style.top  = (rect.top + window.scrollY) + 'px';

        document.body.appendChild(particle);

        // Limpiar después de que termine la animación CSS
        particle.addEventListener('animationend', () => particle.remove());
    }

    // ===================================================
    // 4. INYECTAR ESTILOS CSS
    // ===================================================
    function injectStyles() {
        if (document.getElementById('likes-styles')) return;

        const style = document.createElement('style');
        style.id = 'likes-styles';
        style.textContent = `
            /* === BOTÓN LIKE === */
            .like-btn {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                margin-top: 10px;
                margin-left: 8px;
                padding: 6px 14px;
                border: 1.5px solid #ddd;
                border-radius: 20px;
                background: transparent;
                color: #888;
                font-size: 0.85rem;
                font-family: inherit;
                cursor: pointer;
                transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease, transform 0.15s ease;
                vertical-align: middle;
                user-select: none;
            }

            .like-btn:hover {
                border-color: #e0405a;
                color: #e0405a;
                background: rgba(224, 64, 90, 0.05);
            }

            .like-btn--active {
                border-color: #e0405a;
                color: #e0405a;
                background: rgba(224, 64, 90, 0.08);
            }

            .like-btn--animating {
                transform: scale(1.25);
            }

            /* Icono SVG dentro del botón */
            .like-btn__icon {
                display: flex;
                align-items: center;
            }

            .like-btn__icon svg {
                width: 16px;
                height: 16px;
                transition: fill 0.2s ease;
            }

            .like-btn:hover .like-btn__icon svg,
            .like-btn--active .like-btn__icon svg {
                stroke: #e0405a;
            }

            /* Contador */
            .like-btn__count {
                font-weight: 600;
                min-width: 14px;
                text-align: center;
            }

            /* === PARTÍCULA FLOTANTE === */
            .like-particle {
                position: absolute;
                pointer-events: none;
                z-index: 9999;
                font-size: 1.1rem;
                color: #e0405a;
                animation: like-float 0.7s ease-out forwards;
                transform: translateX(-50%);
            }

            @keyframes like-float {
                0%   { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
                60%  { opacity: 0.8; transform: translateX(-50%) translateY(-28px) scale(1.3); }
                100% { opacity: 0; transform: translateX(-50%) translateY(-50px) scale(0.8); }
            }

            /* Foco accesible */
            .like-btn:focus-visible {
                outline: 2px solid #e0405a;
                outline-offset: 2px;
            }
        `;
        document.head.appendChild(style);
    }

    // ===================================================
    // 5. DELEGACIÓN DE EVENTOS (un solo listener)
    // ===================================================
    function bindEvents() {
        const grid = document.getElementById('noticias') || document.body;
        grid.addEventListener('click', handleLikeClick);
    }

    // ===================================================
    // 6. INICIALIZACIÓN
    // ===================================================
    function init() {
        injectStyles();
        injectLikeButtons();
        bindEvents();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();


/**
 * noticias-header-scroll.js — Junta Distrital de Villa Cutupú
 * Oculta el header al bajar, lo muestra al subir
 */

(function () {
    'use strict';

    // ===================================================
    // UTILIDAD — throttle
    // ===================================================
    function throttle(func, limit) {
        let inThrottle;
        return function () {
            if (!inThrottle) {
                func.apply(this, arguments);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ===================================================
    // HEADER HIDE / SHOW ON SCROLL
    // ===================================================
    const header = document.querySelector('.main-header');
    if (!header) return;

    let lastScrollTop = 0;

    function handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        // Clase scrolled (sombra)
        if (scrollTop > 10) {
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

    window.addEventListener('scroll', throttle(handleScroll, 80));

})();