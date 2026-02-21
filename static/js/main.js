// main.js - Funcionalidad completa para Junta Distrital de Villa Cutupú

document.addEventListener('DOMContentLoaded', function() {
    
    // ===================================================
    // HEADER HIDE ON SCROLL (Ocultar al bajar, mostrar al subir)
    // ===================================================
    const header = document.querySelector('.main-header');
    let lastScrollTop = 0;
    let scrollThreshold = 50; // Mínimo de scroll antes de ocultar
    let headerHeight = header.offsetHeight;
    
    window.addEventListener('scroll', function() {
        let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Agregar/quitar clase scrolled para sombra
        if (scrollTop > 30) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        // Lógica de ocultar/mostrar header
        if (scrollTop > lastScrollTop && scrollTop > headerHeight) {
            // Scroll hacia abajo - ocultar header
            header.classList.add('header-hidden');
        } else {
            // Scroll hacia arriba - mostrar header
            header.classList.remove('header-hidden');
        }
        
        // Actualizar lastScrollTop (evitar valores negativos)
        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    });

    // ===================================================
    // MENÚ MÓVIL - HAMBURGUESA (para cuando el menú esté oculto en móvil)
    // ===================================================
    const createMobileMenu = () => {
        // Solo crear si no existe y estamos en móvil
        if (window.innerWidth <= 768 && !document.querySelector('.mobile-menu-btn')) {
            const nav = document.querySelector('.main-nav ul');
            const headerContainer = document.querySelector('.main-header .container');
            
            // Crear botón hamburguesa
            const mobileBtn = document.createElement('button');
            mobileBtn.className = 'mobile-menu-btn';
            mobileBtn.innerHTML = '☰';
            mobileBtn.setAttribute('aria-label', 'Menú');
            
            // Insertar antes del nav
            headerContainer.insertBefore(mobileBtn, document.querySelector('.main-nav'));
            
            // Crear menú móvil
            const mobileMenu = document.createElement('div');
            mobileMenu.className = 'mobile-menu';
            mobileMenu.innerHTML = nav.cloneNode(true).innerHTML;
            document.body.appendChild(mobileMenu);
            
            // Evento para abrir/cerrar
            mobileBtn.addEventListener('click', function() {
                mobileMenu.classList.toggle('active');
                mobileBtn.classList.toggle('active');
            });
            
            // Cerrar al hacer clic en un enlace
            mobileMenu.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    mobileMenu.classList.remove('active');
                    mobileBtn.classList.remove('active');
                });
            });
        }
    };
    
    // Inicializar menú móvil
    createMobileMenu();
    
    // Re-evaluar en resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            // Eliminar menú móvil si existe
            const mobileMenu = document.querySelector('.mobile-menu');
            const mobileBtn = document.querySelector('.mobile-menu-btn');
            if (mobileMenu) mobileMenu.remove();
            if (mobileBtn) mobileBtn.remove();
        } else {
            createMobileMenu();
        }
    });

    // ===================================================
    // ANIMACIONES AL HACER SCROLL
    // ===================================================
    const animateOnScroll = () => {
        const elements = document.querySelectorAll(
            '.accion-card, .autoridad-card, .vocal-card, .galeria-item, .mensaje-contenido'
        );
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementBottom = element.getBoundingClientRect().bottom;
            const windowHeight = window.innerHeight;
            
            // Si el elemento está en la ventana visible
            if (elementTop < windowHeight - 100 && elementBottom > 0) {
                element.classList.add('fade-in-up');
            }
        });
    };
    
    // Ejecutar al cargar y al hacer scroll
    animateOnScroll();
    window.addEventListener('scroll', animateOnScroll);

    // ===================================================
    // GALERÍA - MODAL PARA VER IMÁGENES
    // ===================================================
    const createImageModal = () => {
        const galleryItems = document.querySelectorAll('.galeria-item');
        
        // Crear modal
        const modal = document.createElement('div');
        modal.className = 'image-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="modal-close">&times;</span>
                <img src="" alt="Imagen ampliada" class="modal-image">
                <p class="modal-caption"></p>
                <button class="modal-prev">❮</button>
                <button class="modal-next">❯</button>
            </div>
        `;
        document.body.appendChild(modal);
        
        let currentIndex = 0;
        const images = Array.from(galleryItems).map(item => ({
            src: item.querySelector('img').src,
            caption: item.querySelector('.galeria-caption')?.textContent || ''
        }));
        
        const openModal = (index) => {
            currentIndex = index;
            const modalImg = modal.querySelector('.modal-image');
            const modalCaption = modal.querySelector('.modal-caption');
            
            modalImg.src = images[currentIndex].src;
            modalCaption.textContent = images[currentIndex].caption;
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        };
        
        galleryItems.forEach((item, index) => {
            item.addEventListener('click', () => openModal(index));
        });
        
        // Controles del modal
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        });
        
        modal.querySelector('.modal-prev').addEventListener('click', () => {
            currentIndex = (currentIndex - 1 + images.length) % images.length;
            openModal(currentIndex);
        });
        
        modal.querySelector('.modal-next').addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % images.length;
            openModal(currentIndex);
        });
        
        // Cerrar con ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
            
            // Navegación con teclas
            if (modal.classList.contains('active')) {
                if (e.key === 'ArrowLeft') {
                    modal.querySelector('.modal-prev').click();
                } else if (e.key === 'ArrowRight') {
                    modal.querySelector('.modal-next').click();
                }
            }
        });
        
        // Cerrar al hacer clic fuera
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    };
    
    // Inicializar modal de galería
    createImageModal();

    // ===================================================
    // SCROLL SUAVE PARA ENLACES INTERNOS
    // ===================================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // ===================================================
    // CONTADOR ANIMADO (para estadísticas si las hay)
    // ===================================================
    const animateCounter = () => {
        const counters = document.querySelectorAll('.counter');
        
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-target'));
            const increment = target / 100;
            let current = 0;
            
            const updateCounter = () => {
                if (current < target) {
                    current += increment;
                    counter.textContent = Math.ceil(current);
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target;
                }
            };
            
            // Verificar si el contador es visible
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        updateCounter();
                        observer.unobserve(entry.target);
                    }
                });
            });
            
            observer.observe(counter);
        });
    };
    
    // Inicializar contadores si existen
    animateCounter();

    // ===================================================
    // BOTÓN VOLVER ARRIBA
    // ===================================================
    const createBackToTop = () => {
        const backBtn = document.createElement('button');
        backBtn.className = 'back-to-top';
        backBtn.innerHTML = '↑';
        backBtn.setAttribute('aria-label', 'Volver arriba');
        document.body.appendChild(backBtn);
        
        window.addEventListener('scroll', () => {
            if (window.scrollY > 500) {
                backBtn.classList.add('visible');
            } else {
                backBtn.classList.remove('visible');
            }
        });
        
        backBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    };
    
    createBackToTop();

    // ===================================================
    // DETECTAR TOQUE EN MÓVILES (para hover effects)
    // ===================================================
    if ('ontouchstart' in window) {
        document.body.classList.add('touch-device');
    }

    // ===================================================
    // CARGAR IMÁGENES CON LAZY LOAD (nativo)
    // ===================================================
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            img.loading = 'lazy';
        });
    }

    // ===================================================
    // PREVENIR CLICKS VACÍOS EN ENLACES
    // ===================================================
    document.querySelectorAll('a[href="#"]').forEach(link => {
        link.addEventListener('click', (e) => e.preventDefault());
    });
});