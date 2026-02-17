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