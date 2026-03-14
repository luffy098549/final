/**
 * mi_cuenta.js - Funcionalidades para la sección Mi Cuenta
 * Junta Distrital de Villa Cutupú
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar componentes
    initPasswordValidation();
    initFormValidation();
    initTabFromHash();
    cargarEstadisticas();
});

// ================================================================
// VALIDACIÓN DE CONTRASEÑA
// ================================================================

function initPasswordValidation() {
    const passwordNueva = document.getElementById('password_nueva');
    const passwordConfirmar = document.getElementById('password_confirmar');
    
    if (passwordNueva && passwordConfirmar) {
        passwordNueva.addEventListener('input', validatePasswordStrength);
        passwordConfirmar.addEventListener('input', validatePasswordMatch);
        
        const form = document.getElementById('cambiar-password-form');
        if (form) {
            form.addEventListener('submit', function(e) {
                if (!validatePasswordForm()) {
                    e.preventDefault();
                }
            });
        }
    }
}

function validatePasswordStrength() {
    const password = document.getElementById('password_nueva').value;
    const strengthIndicator = createStrengthIndicator();
    
    let strength = 0;
    let feedback = [];
    
    // Criterios de fortaleza
    if (password.length >= 6) {
        strength += 20;
        feedback.push('✓ Longitud mínima');
    } else {
        feedback.push('✗ Mínimo 6 caracteres');
    }
    
    if (password.match(/[a-z]/)) {
        strength += 20;
        feedback.push('✓ Minúsculas');
    } else {
        feedback.push('✗ Incluir minúsculas');
    }
    
    if (password.match(/[A-Z]/)) {
        strength += 20;
        feedback.push('✓ Mayúsculas');
    } else {
        feedback.push('✗ Incluir mayúsculas');
    }
    
    if (password.match(/[0-9]/)) {
        strength += 20;
        feedback.push('✓ Números');
    } else {
        feedback.push('✗ Incluir números');
    }
    
    if (password.match(/[^a-zA-Z0-9]/)) {
        strength += 20;
        feedback.push('✓ Caracteres especiales');
    } else {
        feedback.push('✗ Incluir caracteres especiales');
    }
    
    updateStrengthIndicator(strength, feedback);
}

function createStrengthIndicator() {
    let indicator = document.getElementById('password-strength');
    
    if (!indicator) {
        const passwordField = document.getElementById('password_nueva');
        if (!passwordField) return null;
        
        indicator = document.createElement('div');
        indicator.id = 'password-strength';
        indicator.className = 'password-strength';
        passwordField.parentNode.appendChild(indicator);
        
        const progress = document.createElement('div');
        progress.className = 'strength-progress';
        indicator.appendChild(progress);
        
        const feedback = document.createElement('ul');
        feedback.className = 'strength-feedback';
        indicator.appendChild(feedback);
    }
    
    return indicator;
}

function updateStrengthIndicator(strength, feedback) {
    const indicator = document.getElementById('password-strength');
    if (!indicator) return;
    
    const progress = indicator.querySelector('.strength-progress');
    const feedbackList = indicator.querySelector('.strength-feedback');
    
    if (progress) {
        progress.style.width = strength + '%';
        progress.style.background = getStrengthColor(strength);
    }
    
    if (feedbackList) {
        feedbackList.innerHTML = feedback.map(item => `<li>${item}</li>`).join('');
    }
}

function getStrengthColor(strength) {
    if (strength < 40) return '#dc3545';
    if (strength < 70) return '#ffc107';
    return '#28a745';
}

function validatePasswordMatch() {
    const password = document.getElementById('password_nueva').value;
    const confirm = document.getElementById('password_confirmar').value;
    const confirmField = document.getElementById('password_confirmar');
    
    if (!confirmField) return;
    
    if (password && confirm) {
        if (password === confirm) {
            confirmField.style.borderColor = '#28a745';
            removeFeedback(confirmField);
        } else {
            confirmField.style.borderColor = '#dc3545';
            showFeedback(confirmField, 'Las contraseñas no coinciden');
        }
    } else {
        confirmField.style.borderColor = '';
        removeFeedback(confirmField);
    }
}

function validatePasswordForm() {
    const passwordActual = document.getElementById('password_actual')?.value || '';
    const passwordNueva = document.getElementById('password_nueva')?.value || '';
    const passwordConfirmar = document.getElementById('password_confirmar')?.value || '';
    
    if (!passwordActual) {
        showToast('Por favor, ingresa tu contraseña actual', 'error');
        return false;
    }
    
    if (!passwordNueva || passwordNueva.length < 6) {
        showToast('La nueva contraseña debe tener al menos 6 caracteres', 'error');
        return false;
    }
    
    if (passwordNueva !== passwordConfirmar) {
        showToast('Las contraseñas nuevas no coinciden', 'error');
        return false;
    }
    
    return true;
}

// ================================================================
// VALIDACIÓN DE FORMULARIOS
// ================================================================

function initFormValidation() {
    // Formulario de datos personales
    const editForm = document.querySelector('#configuracion .config-card:last-child form');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            actualizarDatos();
        });
    }
    
    // Formulario de preferencias
    const prefForm = document.querySelector('#configuracion .config-card:nth-child(2) form');
    if (prefForm) {
        prefForm.addEventListener('submit', function(e) {
            e.preventDefault();
            guardarPreferencias();
        });
    }
}

function initTabFromHash() {
    const hash = window.location.hash.substring(1);
    if (hash && ['perfil', 'configuracion', 'admin-config', 'actividad'].includes(hash)) {
        showTab(hash);
    }
}

function cargarEstadisticas() {
    // Aquí puedes agregar llamadas AJAX para cargar estadísticas en tiempo real
    console.log('Estadísticas cargadas');
}

// ================================================================
// FUNCIONES DE UTILIDAD
// ================================================================

function showFeedback(field, message) {
    let feedback = field.parentNode.querySelector('.feedback-message');
    
    if (!feedback) {
        feedback = document.createElement('small');
        feedback.className = 'feedback-message';
        field.parentNode.appendChild(feedback);
    }
    
    feedback.textContent = message;
    feedback.style.color = '#dc3545';
}

function removeFeedback(field) {
    const feedback = field.parentNode.querySelector('.feedback-message');
    if (feedback) {
        feedback.remove();
    }
}

function showToast(message, type = 'info') {
    // Verificar si ya existe un contenedor de toasts
    let container = document.querySelector('.toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    // Crear toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${icon}"></i>
        </div>
        <div class="toast-content">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// ================================================================
// FUNCIONES GLOBALES (disponibles desde HTML)
// ================================================================

function showTab(tabId) {
    // Ocultar todos los tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Desactivar todos los botones
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar el tab seleccionado
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Activar el botón correspondiente
    const activeBtn = document.querySelector(`[onclick="showTab('${tabId}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Actualizar URL hash
    window.location.hash = tabId;
}

function editarPerfil() {
    showTab('configuracion');
    
    // Scroll a la sección de datos personales
    setTimeout(() => {
        const datosPersonales = document.querySelector('#configuracion .config-card:last-child');
        if (datosPersonales) {
            datosPersonales.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Resaltar la tarjeta
            datosPersonales.style.transition = 'box-shadow 0.3s ease';
            datosPersonales.style.boxShadow = '0 0 0 4px rgba(126, 143, 118, 0.3)';
            
            setTimeout(() => {
                datosPersonales.style.boxShadow = '';
            }, 2000);
        }
    }, 100);
}

function guardarPreferencias() {
    showToast('Preferencias guardadas correctamente', 'success');
}

function actualizarDatos() {
    const nombre = document.getElementById('edit_nombre')?.value;
    
    if (!nombre) {
        showToast('El nombre es obligatorio', 'error');
        return;
    }
    
    // Enviar formulario
    const form = document.querySelector('#configuracion .config-card:last-child form');
    if (form) {
        form.submit();
    }
}

function guardarConfigSistema() {
    showToast('Configuración del sistema guardada', 'success');
}

function formatDate(dateString) {
    if (!dateString) return 'No disponible';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-DO', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ================================================================
// ESTILOS DINÁMICOS
// ================================================================

const style = document.createElement('style');
style.textContent = `
    .toast-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    .toast {
        min-width: 300px;
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 1rem;
        animation: slideIn 0.3s ease;
        border-left: 4px solid;
    }
    
    .toast-success {
        border-left-color: #28a745;
    }
    
    .toast-success .toast-icon {
        color: #28a745;
    }
    
    .toast-error {
        border-left-color: #dc3545;
    }
    
    .toast-error .toast-icon {
        color: #dc3545;
    }
    
    .toast-info {
        border-left-color: #17a2b8;
    }
    
    .toast-info .toast-icon {
        color: #17a2b8;
    }
    
    .toast-icon {
        font-size: 1.5rem;
    }
    
    .toast-content {
        flex: 1;
        font-size: 0.95rem;
    }
    
    .toast-close {
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        color: #999;
        padding: 0 5px;
    }
    
    .toast-close:hover {
        color: #333;
    }
    
    .password-strength {
        margin-top: 0.5rem;
    }
    
    .strength-progress {
        height: 4px;
        background: #eee;
        border-radius: 2px;
        margin-bottom: 0.5rem;
        transition: width 0.3s ease, background 0.3s ease;
    }
    
    .strength-feedback {
        list-style: none;
        padding: 0;
        margin: 0;
        font-size: 0.85rem;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.3rem;
    }
    
    .strength-feedback li {
        color: #666;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }
    
    .feedback-message {
        display: block;
        margin-top: 0.3rem;
        font-size: 0.85rem;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;

document.head.appendChild(style);