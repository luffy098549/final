// Header ocultable con opciones mejoradas
let lastScrollTop = 0;
const header = document.querySelector('.main-header');
const scrollThreshold = 50; // Mínimo scroll para activar
let ticking = false;

window.addEventListener('scroll', function() {
    if (!ticking) {
        window.requestAnimationFrame(function() {
            let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // Detectar dirección del scroll
            if (scrollTop > lastScrollTop && scrollTop > scrollThreshold) {
                // Scrolling down - Ocultar header
                header.classList.add('header-hidden');
            } else if (scrollTop < lastScrollTop) {
                // Scrolling up - Mostrar header
                header.classList.remove('header-hidden');
            }
            
            // Si estamos en el top, siempre mostrar
            if (scrollTop === 0) {
                header.classList.remove('header-hidden');
            }
            
            lastScrollTop = scrollTop;
            ticking = false;
        });
        
        ticking = true;
    }
});

// Mostrar header cuando el mouse se acerca al top (opcional)
document.addEventListener('mousemove', function(e) {
    if (e.clientY < 50) { // Si el mouse está cerca del top (50px)
        header.classList.remove('header-hidden');
    }
});




/* ============================================================
   main.js — Junta Distrital de Villa Cutupú
   Funciones completas del sitio institucional
   ============================================================ */

/* ===================================================
   1. HEADER — Sombra al hacer scroll
   =================================================== */
function initHeader() {
    const header = document.querySelector('.main-header');
    if (!header) return;

    window.addEventListener('scroll', () => {
        header.classList.toggle('scrolled', window.scrollY > 30);
    }, { passive: true });
}

/* ===================================================
   2. MENÚ HAMBURGUESA — Móvil
   =================================================== */
function initMenuHamburguesa() {
    const nav = document.querySelector('.main-nav');
    if (!nav) return;

    // Crear botón hamburguesa
    const btn = document.createElement('button');
    btn.className = 'menu-toggle';
    btn.setAttribute('aria-label', 'Abrir menú');
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;

    // Insertar antes del nav
    document.querySelector('.main-header .container').appendChild(btn);

    // Estilos del botón via JS (para no depender de CSS extra)
    const style = document.createElement('style');
    style.textContent = `
        .menu-toggle {
            display: none;
            flex-direction: column;
            justify-content: center;
            gap: 5px;
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px;
            border-radius: 8px;
            transition: background-color 0.2s ease;
        }
        .menu-toggle:hover { background: var(--green-xlight); }
        .menu-toggle span {
            display: block;
            width: 22px;
            height: 2px;
            background: var(--text);
            border-radius: 99px;
            transition: transform 0.3s ease, opacity 0.3s ease;
        }
        .menu-toggle.activo span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
        .menu-toggle.activo span:nth-child(2) { opacity: 0; }
        .menu-toggle.activo span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

        @media (max-width: 768px) {
            .menu-toggle { display: flex; }
            .main-nav ul {
                position: fixed;
                top: 68px; left: 0; right: 0;
                background: var(--white);
                border-bottom: 3px solid var(--green);
                flex-direction: column;
                align-items: stretch;
                gap: 0;
                padding: 1rem;
                box-shadow: 0 8px 24px rgba(0,0,0,0.10);
                transform: translateY(-10px);
                opacity: 0;
                pointer-events: none;
                transition: transform 0.3s ease, opacity 0.3s ease;
                z-index: 99;
            }
            .main-nav ul.abierto {
                display: flex !important;
                transform: translateY(0);
                opacity: 1;
                pointer-events: auto;
            }
            .main-nav ul li { width: 100%; }
            .main-nav ul a { display: block; padding: 0.75rem 1rem; border-radius: 8px; }
            .main-nav .btn-login,
            .main-nav .btn-registro { margin: 0.25rem 0; text-align: center; }
        }
    `;
    document.head.appendChild(style);

    const ul = nav.querySelector('ul');

    btn.addEventListener('click', () => {
        const abierto = ul.classList.toggle('abierto');
        btn.classList.toggle('activo', abierto);
        btn.setAttribute('aria-expanded', abierto);
    });

    // Cerrar al hacer click fuera
    document.addEventListener('click', (e) => {
        if (!nav.contains(e.target) && !btn.contains(e.target)) {
            ul.classList.remove('abierto');
            btn.classList.remove('activo');
            btn.setAttribute('aria-expanded', 'false');
        }
    });

    // Cerrar al hacer click en un enlace
    ul.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => {
            ul.classList.remove('abierto');
            btn.classList.remove('activo');
            btn.setAttribute('aria-expanded', 'false');
        });
    });
}

/* ===================================================
   3. ANIMACIONES AL HACER SCROLL (Intersection Observer)
   =================================================== */
function initAnimacionesScroll() {
    const style = document.createElement('style');
    style.textContent = `
        .animar {
            opacity: 0;
            transform: translateY(24px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        .animar.visible {
            opacity: 1;
            transform: translateY(0);
        }
        .animar-delay-1 { transition-delay: 0.1s; }
        .animar-delay-2 { transition-delay: 0.2s; }
        .animar-delay-3 { transition-delay: 0.3s; }
        .animar-delay-4 { transition-delay: 0.4s; }
        .animar-delay-5 { transition-delay: 0.5s; }
    `;
    document.head.appendChild(style);

    // Agregar clase .animar a los elementos
    const selectores = [
        '.accion-card',
        '.autoridad-card',
        '.vocal-card',
        '.galeria-item',
        '.mensaje-contenido',
        '.section-title',
        '.cita-institucional',
        '.info-col'
    ];

    selectores.forEach(sel => {
        document.querySelectorAll(sel).forEach((el, i) => {
            el.classList.add('animar');
            if (i < 5) el.classList.add(`animar-delay-${i + 1}`);
        });
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    document.querySelectorAll('.animar').forEach(el => observer.observe(el));
}

/* ===================================================
   4. SMOOTH SCROLL — Para enlaces internos (#)
   =================================================== */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(enlace => {
        enlace.addEventListener('click', (e) => {
            const id = enlace.getAttribute('href');
            if (id === '#') return;
            const destino = document.querySelector(id);
            if (destino) {
                e.preventDefault();
                destino.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

/* ===================================================
   5. GALERÍA — Lightbox simple al hacer click
   =================================================== */
function initGaleria() {
    const items = document.querySelectorAll('.galeria-item');
    if (!items.length) return;

    // Crear overlay lightbox
    const overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay';
    overlay.innerHTML = `
        <div class="lightbox-contenido">
            <button class="lightbox-cerrar" aria-label="Cerrar">✕</button>
            <img class="lightbox-img" src="" alt="">
            <p class="lightbox-caption"></p>
        </div>
    `;
    document.body.appendChild(overlay);

    const style = document.createElement('style');
    style.textContent = `
        .lightbox-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.88);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        .lightbox-overlay.activo {
            opacity: 1;
            pointer-events: auto;
        }
        .lightbox-contenido {
            position: relative;
            max-width: 900px;
            width: 100%;
            transform: scale(0.95);
            transition: transform 0.3s ease;
        }
        .lightbox-overlay.activo .lightbox-contenido {
            transform: scale(1);
        }
        .lightbox-img {
            width: 100%;
            border-radius: 12px;
            box-shadow: 0 24px 64px rgba(0,0,0,0.5);
        }
        .lightbox-caption {
            color: rgba(255,255,255,0.8);
            text-align: center;
            margin-top: 1rem;
            font-size: 0.95rem;
            font-weight: 500;
        }
        .lightbox-cerrar {
            position: absolute;
            top: -14px;
            right: -14px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: white;
            border: none;
            cursor: pointer;
            font-size: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: transform 0.2s ease;
            z-index: 10;
        }
        .lightbox-cerrar:hover { transform: scale(1.1); }
    `;
    document.head.appendChild(style);

    const img = overlay.querySelector('.lightbox-img');
    const caption = overlay.querySelector('.lightbox-caption');
    const btnCerrar = overlay.querySelector('.lightbox-cerrar');

    function abrir(src, alt, texto) {
        img.src = src;
        img.alt = alt;
        caption.textContent = texto;
        overlay.classList.add('activo');
        document.body.style.overflow = 'hidden';
    }

    function cerrar() {
        overlay.classList.remove('activo');
        document.body.style.overflow = '';
    }

    items.forEach(item => {
        item.style.cursor = 'pointer';
        item.addEventListener('click', () => {
            const imgEl = item.querySelector('img');
            const cap = item.querySelector('.galeria-caption');
            if (imgEl) abrir(imgEl.src, imgEl.alt, cap ? cap.textContent : '');
        });
    });

    btnCerrar.addEventListener('click', cerrar);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) cerrar();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') cerrar();
    });
}

/* ===================================================
   6. CONTADOR ANIMADO — Para estadísticas (si las usas)
   Uso: <span class="contador" data-target="5000">0</span>
   =================================================== */
function initContadores() {
    const contadores = document.querySelectorAll('.contador');
    if (!contadores.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;

            const el = entry.target;
            const target = parseInt(el.dataset.target, 10);
            const duracion = 1800;
            const inicio = performance.now();

            function actualizar(ahora) {
                const progreso = Math.min((ahora - inicio) / duracion, 1);
                const easing = 1 - Math.pow(1 - progreso, 3);
                el.textContent = Math.floor(easing * target).toLocaleString('es-DO');
                if (progreso < 1) requestAnimationFrame(actualizar);
            }

            requestAnimationFrame(actualizar);
            observer.unobserve(el);
        });
    }, { threshold: 0.5 });

    contadores.forEach(el => observer.observe(el));
}

/* ===================================================
   7. TOOLTIP en vocales — Muestra nombre completo al hover
   =================================================== */
function initTooltipsVocales() {
    const style = document.createElement('style');
    style.textContent = `
        .vocal-card { position: relative; }
        .vocal-tooltip {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%);
            background: var(--gray-900);
            color: white;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            white-space: nowrap;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
            z-index: 10;
        }
        .vocal-tooltip::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 5px solid transparent;
            border-top-color: var(--gray-900);
        }
        .vocal-card:hover .vocal-tooltip { opacity: 1; }
    `;
    document.head.appendChild(style);

    document.querySelectorAll('.vocal-card').forEach(card => {
        const nombre = card.querySelector('.vocal-name')?.textContent;
        if (!nombre) return;
        const tooltip = document.createElement('div');
        tooltip.className = 'vocal-tooltip';
        tooltip.textContent = nombre;
        card.appendChild(tooltip);
    });
}

/* ===================================================
   8. BOTÓN "VOLVER ARRIBA"
   =================================================== */
function initBotonArriba() {
    const btn = document.createElement('button');
    btn.className = 'btn-arriba';
    btn.setAttribute('aria-label', 'Volver arriba');
    btn.innerHTML = '↑';
    document.body.appendChild(btn);

    const style = document.createElement('style');
    style.textContent = `
        .btn-arriba {
            position: fixed;
            bottom: 90px;
            right: 28px;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background: var(--white);
            color: var(--green);
            border: 2px solid var(--green);
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: var(--shadow-md);
            z-index: 98;
            opacity: 0;
            transform: translateY(10px);
            transition: opacity 0.3s ease,
                        transform 0.3s ease,
                        background-color 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .btn-arriba.visible {
            opacity: 1;
            transform: translateY(0);
        }
        .btn-arriba:hover {
            background: var(--green);
            color: white;
        }
    `;
    document.head.appendChild(style);

    window.addEventListener('scroll', () => {
        btn.classList.toggle('visible', window.scrollY > 400);
    }, { passive: true });

    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

/* ===================================================
   9. ACTIVE NAV — Marca el enlace activo según la URL
   =================================================== */
function initNavActivo() {
    const ruta = window.location.pathname;
    document.querySelectorAll('.main-nav a').forEach(a => {
        const href = a.getAttribute('href');
        if (href === ruta || (ruta === '/' && href === '/')) {
            a.style.color = 'var(--green-dark)';
            a.style.background = 'var(--green-xlight)';
            a.style.fontWeight = '700';
        }
    });
}

/* ===================================================
   10. LAZY LOADING — Imágenes con fade in
   =================================================== */
function initLazyImages() {
    const style = document.createElement('style');
    style.textContent = `
        img[loading="lazy"] {
            opacity: 0;
            transition: opacity 0.4s ease;
        }
        img[loading="lazy"].cargada {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);

    document.querySelectorAll('img[loading="lazy"]').forEach(img => {
        if (img.complete) {
            img.classList.add('cargada');
        } else {
            img.addEventListener('load', () => img.classList.add('cargada'));
        }
    });
}

/* ===================================================
   INICIALIZACIÓN — Ejecutar todo cuando el DOM esté listo
   =================================================== */
document.addEventListener('DOMContentLoaded', () => {
    initHeader();
    initMenuHamburguesa();
    initAnimacionesScroll();
    initSmoothScroll();
    initGaleria();
    initContadores();
    initTooltipsVocales();
    initBotonArriba();
    initNavActivo();
    initLazyImages();
});




/* ============================================================
   header.js — Ocultar header al bajar, mostrar al subir
   ============================================================ */

function initHeaderScroll() {
    const header = document.querySelector('.main-header');
    if (!header) return;

    // CSS necesario
    const style = document.createElement('style');
    style.textContent = `
        .main-header {
            transition: transform 0.35s ease, box-shadow 0.3s ease;
        }
        .main-header.oculto {
            transform: translateY(-100%);
        }
        .main-header.scrolled {
            box-shadow: 0 4px 20px rgba(0,0,0,0.10);
        }
    `;
    document.head.appendChild(style);

    let scrollAnterior = 0;
    const UMBRAL = 60; // píxeles mínimos antes de reaccionar

    window.addEventListener('scroll', () => {
        const scrollActual = window.scrollY;

        // Sombra al bajar de 30px
        header.classList.toggle('scrolled', scrollActual > 30);

        // Siempre visible en la parte superior
        if (scrollActual <= UMBRAL) {
            header.classList.remove('oculto');
            scrollAnterior = scrollActual;
            return;
        }

        if (scrollActual > scrollAnterior) {
            // Bajando → ocultar
            header.classList.add('oculto');
        } else {
            // Subiendo → mostrar
            header.classList.remove('oculto');
        }

        scrollAnterior = scrollActual;
    }, { passive: true });
}

document.addEventListener('DOMContentLoaded', initHeaderScroll);