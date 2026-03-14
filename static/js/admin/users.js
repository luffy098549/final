// ============================================================
// admin-users.js - Gestión de Administradores
// ============================================================

// ===== VARIABLES GLOBALES =====
let adminEditando = null;

// ===== FUNCIONES DE MODALES =====
function openCrearAdminModal() {
    document.getElementById('modalCrearAdmin').style.display = 'flex';
    document.getElementById('formCrearAdmin').reset();
    document.getElementById('passwordStrength').innerHTML = '';
}

function openCambiarPasswordModal() {
    document.getElementById('modalCambiarPassword').style.display = 'flex';
    document.getElementById('formCambiarPassword').reset();
    document.getElementById('strengthBar').style.width = '0%';
    document.getElementById('passwordMatchMessage').innerHTML = '';
}

function cerrarModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// ===== FILTRAR ADMINISTRADORES =====
function filtrarAdmins() {
    const searchTerm = document.getElementById('searchAdmin').value.toLowerCase();
    const rolFilter = document.getElementById('rolFilter').value;
    const estadoFilter = document.getElementById('estadoFilter').value;
    
    const rows = document.querySelectorAll('.admin-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const nombre = row.dataset.nombre.toLowerCase();
        const email = row.dataset.email.toLowerCase();
        const rol = row.dataset.role;
        const estado = row.dataset.estado;
        
        const matchesSearch = nombre.includes(searchTerm) || email.includes(searchTerm);
        const matchesRol = rolFilter === 'todos' || rol === rolFilter;
        const matchesEstado = estadoFilter === 'todos' || estado === estadoFilter;
        
        if (matchesSearch && matchesRol && matchesEstado) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Mostrar mensaje si no hay resultados
    const noResults = document.getElementById('noResultsMessage');
    if (visibleCount === 0) {
        noResults.style.display = 'flex';
    } else {
        noResults.style.display = 'none';
    }
}

// ===== ESTADÍSTICAS =====
function inicializarEstadisticas() {
    const rows = document.querySelectorAll('.admin-row');
    let superAdmins = 0, admins = 0, moderadores = 0, activos = 0;
    
    rows.forEach(row => {
        const rol = row.dataset.role;
        const estado = row.dataset.estado;
        
        if (rol === 'super_admin') superAdmins++;
        if (rol === 'admin') admins++;
        if (rol === 'moderador') moderadores++;
        if (estado === 'activo') activos++;
    });
    
    document.getElementById('totalSuperAdmins').textContent = superAdmins;
    document.getElementById('totalAdmins').textContent = admins;
    document.getElementById('totalModeradores').textContent = moderadores;
    document.getElementById('totalActivos').textContent = activos;
}

// ===== GENERAR CONTRASEÑA =====
function generarPassword() {
    const length = 10;
    const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
    let password = "";
    
    // Asegurar al menos una mayúscula, una minúscula, un número y un especial
    password += "A" + "a" + "1" + "!";
    
    for (let i = 0; i < length - 4; i++) {
        const randomIndex = Math.floor(Math.random() * charset.length);
        password += charset[randomIndex];
    }
    
    // Mezclar la contraseña
    password = password.split('').sort(() => Math.random() - 0.5).join('');
    
    document.getElementById('adminPassword').value = password;
    checkPasswordStrength(document.getElementById('adminPassword').value);
}

function generarPasswordAdmin() {
    const length = 12;
    const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
    let password = "";
    
    for (let i = 0; i < length; i++) {
        const randomIndex = Math.floor(Math.random() * charset.length);
        password += charset[randomIndex];
    }
    
    document.getElementById('passwordNuevaAdmin').value = password;
    document.getElementById('passwordConfirmarAdmin').value = password;
}

// ===== VALIDAR CONTRASEÑA =====
function checkPasswordStrength(password) {
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('passwordStrength');
    
    if (!strengthBar || !strengthText) return;
    
    let strength = 0;
    
    if (password.length >= 8) strength += 25;
    if (password.match(/[a-z]+/)) strength += 25;
    if (password.match(/[A-Z]+/)) strength += 25;
    if (password.match(/[0-9]+/)) strength += 15;
    if (password.match(/[$@#&!]+/)) strength += 10;
    
    strengthBar.style.width = strength + '%';
    
    if (strength < 40) {
        strengthBar.style.background = '#ef4444';
        strengthText.innerHTML = 'Contraseña débil';
    } else if (strength < 70) {
        strengthBar.style.background = '#f59e0b';
        strengthText.innerHTML = 'Contraseña media';
    } else {
        strengthBar.style.background = '#10b981';
        strengthText.innerHTML = 'Contraseña fuerte';
    }
}

function validatePasswordMatch() {
    const nueva = document.getElementById('passwordNueva').value;
    const confirmar = document.getElementById('passwordConfirmar').value;
    const message = document.getElementById('passwordMatchMessage');
    const btn = document.getElementById('btnCambiarPassword');
    
    if (nueva && confirmar) {
        if (nueva === confirmar) {
            message.innerHTML = '✓ Las contraseñas coinciden';
            message.style.color = '#10b981';
            btn.disabled = false;
        } else {
            message.innerHTML = '✗ Las contraseñas no coinciden';
            message.style.color = '#ef4444';
            btn.disabled = true;
        }
    }
}

function setupPasswordValidation() {
    const passwordInput = document.getElementById('passwordNueva');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            checkPasswordStrength(this.value);
            validatePasswordMatch();
        });
    }
}

// ===== CREAR ADMINISTRADOR =====
async function crearAdmin(event) {
    event.preventDefault();
    
    const formData = {
        nombre: document.getElementById('adminNombre').value,
        apellidos: document.getElementById('adminApellidos').value,
        email: document.getElementById('adminEmail').value,
        telefono: document.getElementById('adminTelefono').value,
        rol: document.getElementById('adminRol').value,
        password: document.getElementById('adminPassword').value,
        notas: document.getElementById('adminNotas').value,
        permisos: {
            usuarios: document.getElementById('permUsuarios').checked,
            solicitudes: document.getElementById('permSolicitudes').checked,
            denuncias: document.getElementById('permDenuncias').checked,
            config: document.getElementById('permConfig').checked,
            reportes: document.getElementById('permReportes').checked,
            bitacora: document.getElementById('permBitacora').checked
        }
    };
    
    try {
        const response = await fetch('/admin/api/crear-admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarToast('✅ Administrador creado correctamente', 'success');
            cerrarModal('modalCrearAdmin');
            setTimeout(() => location.reload(), 1500);
        } else {
            mostrarToast('❌ Error: ' + data.message, 'error');
        }
    } catch (error) {
        mostrarToast('❌ Error de conexión', 'error');
    }
}

// ===== EDITAR ADMIN =====
function editarAdmin(email) {
    // Buscar datos del admin
    const row = document.querySelector(`[data-email="${email}"]`);
    if (!row) return;
    
    document.getElementById('editEmail').value = email;
    document.getElementById('editNombre').value = row.dataset.nombre.split(' ')[0];
    document.getElementById('editApellidos').value = row.dataset.nombre.split(' ').slice(1).join(' ');
    
    // Aquí deberías cargar más datos desde el backend
    document.getElementById('modalEditarAdmin').style.display = 'flex';
}

async function editarAdminSubmit(event) {
    event.preventDefault();
    
    const formData = {
        email: document.getElementById('editEmail').value,
        nombre: document.getElementById('editNombre').value,
        apellidos: document.getElementById('editApellidos').value,
        telefono: document.getElementById('editTelefono').value,
        rol: document.getElementById('editRol').value,
        notas: document.getElementById('editNotas').value
    };
    
    try {
        const response = await fetch('/admin/api/editar-admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarToast('✅ Administrador actualizado', 'success');
            cerrarModal('modalEditarAdmin');
            setTimeout(() => location.reload(), 1500);
        } else {
            mostrarToast('❌ Error: ' + data.message, 'error');
        }
    } catch (error) {
        mostrarToast('❌ Error de conexión', 'error');
    }
}

// ===== CAMBIAR CONTRASEÑA (Propia) =====
async function cambiarMiPassword(event) {
    event.preventDefault();
    
    const formData = {
        password_actual: document.getElementById('passwordActual').value,
        password_nueva: document.getElementById('passwordNueva').value,
        password_confirmar: document.getElementById('passwordConfirmar').value
    };
    
    try {
        const response = await fetch('/auth/cambiar-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarToast('✅ Contraseña actualizada correctamente', 'success');
            cerrarModal('modalCambiarPassword');
            document.getElementById('formCambiarPassword').reset();
        } else {
            mostrarToast('❌ ' + data.message, 'error');
        }
    } catch (error) {
        mostrarToast('❌ Error de conexión', 'error');
    }
}

// ===== CAMBIAR CONTRASEÑA DE OTRO ADMIN =====
function cambiarPasswordAdmin(email, nombre) {
    document.getElementById('adminEmailCambio').value = email;
    document.getElementById('adminNombreCambio').textContent = nombre;
    document.getElementById('modalCambiarPasswordAdmin').style.display = 'flex';
}

async function cambiarPasswordAdminSubmit(event) {
    event.preventDefault();
    
    const formData = {
        email: document.getElementById('adminEmailCambio').value,
        password_nueva: document.getElementById('passwordNuevaAdmin').value,
        password_confirmar: document.getElementById('passwordConfirmarAdmin').value,
        notificar: document.getElementById('notificarUsuario').checked
    };
    
    try {
        const response = await fetch('/admin/api/cambiar-password-admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarToast('✅ Contraseña actualizada', 'success');
            cerrarModal('modalCambiarPasswordAdmin');
        } else {
            mostrarToast('❌ ' + data.message, 'error');
        }
    } catch (error) {
        mostrarToast('❌ Error de conexión', 'error');
    }
}

// ===== TOGGLE ESTADO ADMIN =====
async function toggleEstadoAdmin(email, estadoActual) {
    const nuevoEstado = !estadoActual;
    const accion = nuevoEstado ? 'activar' : 'desactivar';
    
    if (!confirm(`¿Estás seguro de ${accion} este administrador?`)) return;
    
    try {
        const response = await fetch('/admin/api/toggle-estado-admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, activo: nuevoEstado })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarToast(`✅ Administrador ${accion}do`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            mostrarToast('❌ Error al cambiar estado', 'error');
        }
    } catch (error) {
        mostrarToast('❌ Error de conexión', 'error');
    }
}

// ===== TOAST NOTIFICATIONS =====
function mostrarToast(mensaje, tipo = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = mensaje;
    toast.className = `toast ${tipo}`;
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// ===== CERRAR MODALES CON CLICK FUERA =====
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// ===== CERRAR CON ESC =====
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }
});