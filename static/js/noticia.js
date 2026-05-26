/**
 * noticia.js - Junta Distrital de Villa Cutupú
 * Sistema de Likes para tarjetas de noticias
 * Versión 2.0 — Sin inyección de botones (usan los del template)
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'cutupu_likes';

    // ===================================================
    // UTILIDADES
    // ===================================================
    function getLikesData() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
        catch (e) { return {}; }
    }

    function saveLikesData(data) {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); }
        catch (e) { console.warn('[Likes] localStorage no disponible:', e); }
    }

    function getLikedByUser() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY + '_user');
            return new Set(JSON.parse(raw) || []);
        } catch (e) { return new Set(); }
    }

    function saveLikedByUser(set) {
        try { localStorage.setItem(STORAGE_KEY + '_user', JSON.stringify([...set])); }
        catch (e) { console.warn('[Likes] localStorage no disponible:', e); }
    }

    // ===================================================
    // INICIALIZAR ESTADO DE BOTONES EXISTENTES EN EL HTML
    // ===================================================
    function initExistingButtons() {
        const buttons = document.querySelectorAll('.like-btn');
        if (!buttons.length) return;

        const likesData   = getLikesData();
        const likedByUser = getLikedByUser();

        buttons.forEach(btn => {
            const slug = btn.dataset.slug;
            if (!slug) return;

            // Sincronizar contador: prioridad al localStorage, si no al data-likes del HTML
            const storedCount = likesData[slug];
            const htmlCount   = parseInt(btn.dataset.likes, 10) || 0;
            const count       = storedCount !== undefined ? storedCount : htmlCount;

            const countEl = btn.querySelector('.like-count');
            if (countEl) countEl.textContent = count;

            // Marcar si ya le dio like
            if (likedByUser.has(slug)) {
                btn.classList.add('liked');
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                }
            }
        });
    }

    // ===================================================
    // LÓGICA DE LIKE / UNLIKE
    // ===================================================
    function handleLikeClick(e) {
        const btn = e.target.closest('.like-btn');
        if (!btn) return;

        // Evitar doble clic durante animación
        if (btn.disabled) return;

        const slug        = btn.dataset.slug;
        if (!slug) return;

        const likesData   = getLikesData();
        const likedByUser = getLikedByUser();
        const countEl     = btn.querySelector('.like-count');
        const icon        = btn.querySelector('i');
        const isLiked     = likedByUser.has(slug);

        if (isLiked) {
            // Unlike
            likedByUser.delete(slug);
            likesData[slug] = Math.max(0, (likesData[slug] || 1) - 1);
            btn.classList.remove('liked');
            if (icon) { icon.classList.remove('fas'); icon.classList.add('far'); }
            btn.setAttribute('aria-pressed', 'false');
        } else {
            // Like
            likedByUser.add(slug);
            likesData[slug] = (likesData[slug] || 0) + 1;
            btn.classList.add('liked');
            if (icon) { icon.classList.remove('far'); icon.classList.add('fas'); }
            btn.setAttribute('aria-pressed', 'true');
            spawnHeartParticle(btn);
        }

        if (countEl) countEl.textContent = likesData[slug];

        saveLikesData(likesData);
        saveLikedByUser(likedByUser);
    }

    // ===================================================
    // PARTÍCULA FLOTANTE
    // ===================================================
    function spawnHeartParticle(btn) {
        const particle = document.createElement('span');
        particle.setAttribute('aria-hidden', 'true');
        particle.textContent = '♥';
        particle.style.cssText = `
            position: fixed;
            pointer-events: none;
            z-index: 9999;
            font-size: 1.1rem;
            color: #e74c3c;
            animation: likeFloat 0.7s ease-out forwards;
            transform: translateX(-50%);
        `;

        const rect = btn.getBoundingClientRect();
        particle.style.left = (rect.left + rect.width / 2) + 'px';
        particle.style.top  = rect.top + 'px';

        document.body.appendChild(particle);
        particle.addEventListener('animationend', () => particle.remove());
    }

    // ===================================================
    // KEYFRAME DE PARTÍCULA (inyectado una sola vez)
    // ===================================================
    function injectParticleStyle() {
        if (document.getElementById('like-particle-style')) return;
        const style = document.createElement('style');
        style.id = 'like-particle-style';
        style.textContent = `
            @keyframes likeFloat {
                0%   { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
                60%  { opacity: 0.8; transform: translateX(-50%) translateY(-28px) scale(1.3); }
                100% { opacity: 0; transform: translateX(-50%) translateY(-50px) scale(0.8); }
            }
        `;
        document.head.appendChild(style);
    }

    // ===================================================
    // HEADER HIDE / SHOW ON SCROLL
    // ===================================================
    function initHeaderScroll() {
        const header = document.querySelector('.main-header');
        if (!header) return;

        let lastScrollTop = 0;

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

        function handleScroll() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            header.classList.toggle('scrolled', scrollTop > 10);
            if (scrollTop > lastScrollTop && scrollTop > header.offsetHeight) {
                header.classList.add('header-hidden');
            } else {
                header.classList.remove('header-hidden');
            }
            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        }

        window.addEventListener('scroll', throttle(handleScroll, 80));
    }

    // ===================================================
    // INIT
    // ===================================================
    function init() {
        injectParticleStyle();
        initExistingButtons();

        // Un solo listener delegado para todos los likes
        const grid = document.getElementById('noticias') || document.body;
        grid.addEventListener('click', handleLikeClick);

        initHeaderScroll();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();