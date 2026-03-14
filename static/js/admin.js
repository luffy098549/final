// ============================================================
// VILLA CUTUPÚ — Sidebar & Mobile Menu Fix
// Reemplaza la lógica de initAdminInterface() en admin.js
// ============================================================

function initAdminInterface() {
    const sidebar       = document.getElementById('sidebar');
    const toggleBtn     = document.getElementById('sidebarToggle');
    const mobileToggle  = document.getElementById('mobileMenuToggle');
    const mainContent   = document.getElementById('mainContent');

    // ── Collapse (desktop) ──────────────────────────────────
    if (toggleBtn && sidebar) {
        // Restaurar estado guardado
        const collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (collapsed) {
            sidebar.classList.add('collapsed');
            document.body.classList.add('sidebar-collapsed');
        }

        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            const isCollapsed = sidebar.classList.contains('collapsed');
            document.body.classList.toggle('sidebar-collapsed', isCollapsed);
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });
    }

    // ── Mobile menu ─────────────────────────────────────────
    if (mobileToggle && sidebar) {
        // Crear overlay si no existe
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
        }

        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        });

        overlay.addEventListener('click', () => {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    // ── Notificaciones dropdown ──────────────────────────────
    const notifBtn      = document.getElementById('notificationsBtn');
    const notifDropdown = document.getElementById('notificationsDropdown');

    if (notifBtn && notifDropdown) {
        notifBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notifDropdown.classList.toggle('show');
            profileDropdown?.classList.remove('show');
        });
    }

    // ── Perfil dropdown ──────────────────────────────────────
    const profileBtn      = document.getElementById('profileBtn');
    const profileDropdown = document.getElementById('profileDropdown');

    if (profileBtn && profileDropdown) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profileDropdown.classList.toggle('show');
            notifDropdown?.classList.remove('show');
        });
    }

    // Cerrar dropdowns al hacer click fuera
    document.addEventListener('click', () => {
        notifDropdown?.classList.remove('show');
        profileDropdown?.classList.remove('show');
    });

    // ── Tooltips en sidebar colapsado ────────────────────────
    // Añade data-tooltip a cada enlace del nav con el texto del span
    document.querySelectorAll('.admin-sidebar-nav a').forEach(link => {
        const span = link.querySelector('span:first-of-type');
        if (span && !link.dataset.tooltip) {
            link.dataset.tooltip = span.textContent.trim();
        }
    });
}

// Búsqueda global
function setupGlobalSearch() {
    const input  = document.getElementById('globalSearch');
    const modal  = document.getElementById('searchModal');

    if (!input || !modal) return;

    // Ctrl+K abre el modal
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openSearchModal();
        }
        if (e.key === 'Escape') closeSearchModal();
    });

    input.addEventListener('click', openSearchModal);
}

function openSearchModal() {
    const modal = document.getElementById('searchModal');
    const searchInput = document.getElementById('searchInput');
    modal?.classList.add('show');
    setTimeout(() => searchInput?.focus(), 50);
}

function closeSearchModal() {
    document.getElementById('searchModal')?.classList.remove('show');
}