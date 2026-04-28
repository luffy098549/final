// static/js/noticia.js
// Sistema de likes para noticias (versión API)

(function() {
    'use strict';

    /**
     * Inyecta los estilos CSS necesarios para el botón de like
     * y las animaciones (se mantiene igual)
     */
    function injectStyles() {
        if (document.getElementById('noticia-like-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'noticia-like-styles';
        style.textContent = `
            /* Botón Like */
            .like-btn {
                background: transparent;
                border: 2px solid #e0e0e0;
                border-radius: 40px;
                padding: 0.6rem 1.2rem;
                font-size: 0.9rem;
                font-weight: 600;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 0.6rem;
                transition: all 0.3s ease;
                color: #666;
            }
            .like-btn:hover {
                border-color: #e74c3c;
                transform: scale(1.02);
            }
            .like-btn.liked {
                background: #e74c3c;
                border-color: #e74c3c;
                color: white;
            }
            .like-btn.liked i {
                color: white;
            }
            .like-btn i {
                font-size: 1.1rem;
                transition: transform 0.2s ease;
                color: #666;
            }
            .like-btn:active {
                transform: scale(0.95);
            }
            .like-count {
                font-weight: 700;
            }
            /* Corazón animación flotante */
            .heart-particle {
                position: fixed;
                color: #e74c3c;
                font-size: 1.5rem;
                pointer-events: none;
                z-index: 9999;
                animation: floatUp 1s ease-out forwards;
            }
            @keyframes floatUp {
                0% {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
                100% {
                    opacity: 0;
                    transform: translateY(-80px) scale(1.5);
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Dispara animación del corazón (efecto visual)
     */
    function triggerLikeAnimation(btn) {
        const rect = btn.getBoundingClientRect();
        const heart = document.createElement('div');
        heart.className = 'heart-particle';
        heart.innerHTML = '<i class="fas fa-heart"></i>';
        heart.style.left = rect.left + rect.width / 2 - 15 + 'px';
        heart.style.top = rect.top - 20 + 'px';
        document.body.appendChild(heart);
        
        setTimeout(() => {
            if (heart.parentNode) heart.remove();
        }, 1000);
    }

    /**
     * Genera múltiples partículas de corazón (efecto explosión)
     */
    function spawnHeartParticle(btn, count = 5) {
        for (let i = 0; i < count; i++) {
            setTimeout(() => {
                triggerLikeAnimation(btn);
            }, i * 50);
        }
    }

    /**
     * Construye el HTML del botón like
     * El estado 'liked' viene del atributo data-liked en el servidor
     */
    function buildLikeButton(slug, liked, likesCount) {
        const heartIcon = liked ? 'fas fa-heart' : 'far fa-heart';
        return `
            <button class="like-btn" data-slug="${slug}" data-liked="${liked}" data-likes="${likesCount}">
                <i class="${heartIcon}"></i>
                <span class="like-count">${likesCount}</span>
                <span class="like-text">${liked ? 'Te gusta' : 'Me gusta'}</span>
            </button>
        `;
    }

    /**
     * Actualiza el estado visual del botón (sin recargar la página)
     */
    function updateButtonVisual(btn, liked, likesCount) {
        const icon = btn.querySelector('i');
        const countSpan = btn.querySelector('.like-count');
        const textSpan = btn.querySelector('.like-text');
        
        if (liked) {
            icon.className = 'fas fa-heart';
            textSpan.textContent = 'Te gusta';
            btn.classList.add('liked');
        } else {
            icon.className = 'far fa-heart';
            textSpan.textContent = 'Me gusta';
            btn.classList.remove('liked');
        }
        
        if (countSpan) {
            countSpan.textContent = likesCount;
        }
        
        btn.setAttribute('data-liked', liked);
        btn.setAttribute('data-likes', likesCount);
    }

    /**
     * Maneja el click en el botón LIKE
     * Envía POST a la API del servidor y actualiza el estado
     */
    async function handleLikeClick(btn, slug) {
        // Obtener estado actual desde el atributo data-liked (viene del servidor)
        const currentlyLiked = btn.getAttribute('data-liked') === 'true';
        
        // Deshabilitar botón durante la petición
        btn.disabled = true;
        
        // Guardar texto original para posibles errores
        const originalText = btn.innerHTML;
        
        // Agregar clase de loading (opcional)
        btn.style.opacity = '0.7';
        
        try {
            const response = await fetch(`/api/noticias/${slug}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (response.ok && data.ok) {
                // Actualizar estado visual según respuesta del servidor
                updateButtonVisual(btn, data.liked, data.total);
                
                // Si el nuevo estado es "like" (data.liked === true)
                if (data.liked === true) {
                    spawnHeartParticle(btn, 4);
                }
            } else {
                // Error de API, mantener estado anterior
                console.warn('Error en like API:', data.mensaje || 'Error desconocido');
                // Recuperar estado original visualmente
                updateButtonVisual(btn, currentlyLiked, parseInt(btn.getAttribute('data-likes')) || 0);
            }
        } catch (error) {
            console.error('Error de red al enviar like:', error);
            // En caso de error de red, mantener el estado anterior
            updateButtonVisual(btn, currentlyLiked, parseInt(btn.getAttribute('data-likes')) || 0);
        } finally {
            // Rehabilitar botón
            btn.disabled = false;
            btn.style.opacity = '';
        }
    }

    /**
     * Itera sobre todos los botones like y registra el evento
     */
    function injectLikeButtons() {
        const likeButtons = document.querySelectorAll('.like-btn');
        
        likeButtons.forEach(btn => {
            // Evitar duplicar event listeners
            if (btn.hasAttribute('data-listener')) return;
            
            const slug = btn.getAttribute('data-slug');
            if (!slug) return;
            
            btn.setAttribute('data-listener', 'true');
            
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                handleLikeClick(btn, slug);
            });
        });
    }

    /**
     * Inicializa todo el sistema
     */
    function init() {
        injectStyles();
        injectLikeButtons();
        
        // Observador para botones que se cargan dinámicamente
        const observer = new MutationObserver(() => {
            injectLikeButtons();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

// ================================================================
// HEADER SCROLL (mantener igual)
// ================================================================
(function() {
    const header = document.querySelector('.main-header');
    if (!header) return;

    let lastScrollTop = 0;
    let ticking = false;

    function updateHeader() {
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        
        if (currentScroll > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        if (currentScroll > lastScrollTop && currentScroll > header.offsetHeight) {
            header.classList.add('header-hidden');
        } else {
            header.classList.remove('header-hidden');
        }
        
        lastScrollTop = Math.max(0, currentScroll);
        ticking = false;
    }

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(updateHeader);
            ticking = true;
        }
    });
    
    updateHeader();
})();