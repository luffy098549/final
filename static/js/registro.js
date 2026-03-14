/**
 * registro.js - Sistema de registro profesional
 * Junta Distrital Villa Cutupú
 * Versión 3.0 - SIMPLIFICADO
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el formulario de registro
    initRegistroForm();
});

function initRegistroForm() {
    const form = document.getElementById('registroForm');
    if (!form) return;

    // Elementos del DOM
    const steps = document.querySelectorAll('.form-step');
    const progressSteps = document.querySelectorAll('.progress-step');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    let currentStep = 1;
    const totalSteps = 4;

    // ===== FORMATEO EN TIEMPO REAL =====
    
    // 1. CÉDULA - SOLO NÚMEROS, MÁXIMO 11 DÍGITOS
    const cedulaInput = document.getElementById('cedula');
    if (cedulaInput) {
        cedulaInput.addEventListener('input', function(e) {
            // Eliminar cualquier carácter que no sea número
            let value = this.value.replace(/\D/g, '');
            
            // Limitar a 11 dígitos
            if (value.length > 11) {
                value = value.slice(0, 11);
            }
            
            // Actualizar el valor
            this.value = value;
            
            // Feedback visual
            const feedback = getOrCreateFeedback(this);
            if (value.length === 11) {
                this.classList.add('valid');
                this.classList.remove('error');
                feedback.innerHTML = '<i class="fas fa-check-circle" style="color: #28a745;"></i> Cédula válida';
                feedback.style.color = '#28a745';
            } else if (value.length > 0) {
                this.classList.add('error');
                this.classList.remove('valid');
                feedback.innerHTML = `<i class="fas fa-exclamation-circle" style="color: #dc3545;"></i> Faltan ${11 - value.length} dígitos`;
                feedback.style.color = '#dc3545';
            } else {
                this.classList.remove('valid', 'error');
                feedback.innerHTML = '';
            }
        });

        // Validar al salir del campo
        cedulaInput.addEventListener('blur', function() {
            if (this.value.length > 0 && this.value.length !== 11) {
                showFieldError(this, `La cédula debe tener 11 dígitos (actual: ${this.value.length})`);
            }
        });
    }

    // 2. TELÉFONO - SOLO NÚMEROS, MÁXIMO 10 DÍGITOS
    const telefonoInput = document.getElementById('telefono');
    if (telefonoInput) {
        telefonoInput.addEventListener('input', function(e) {
            // Eliminar cualquier carácter que no sea número
            let value = this.value.replace(/\D/g, '');
            
            // Limitar a 10 dígitos
            if (value.length > 10) {
                value = value.slice(0, 10);
            }
            
            // Actualizar el valor
            this.value = value;
            
            // Feedback visual
            const feedback = getOrCreateFeedback(this);
            if (value.length === 10) {
                this.classList.add('valid');
                this.classList.remove('error');
                feedback.innerHTML = '<i class="fas fa-check-circle" style="color: #28a745;"></i> Teléfono válido';
                feedback.style.color = '#28a745';
            } else if (value.length > 0) {
                this.classList.add('error');
                this.classList.remove('valid');
                feedback.innerHTML = `<i class="fas fa-exclamation-circle" style="color: #dc3545;"></i> Faltan ${10 - value.length} dígitos`;
                feedback.style.color = '#dc3545';
            } else {
                this.classList.remove('valid', 'error');
                feedback.innerHTML = '';
            }
        });

        // Validar al salir del campo
        telefonoInput.addEventListener('blur', function() {
            if (this.value.length > 0 && this.value.length !== 10) {
                showFieldError(this, `El teléfono debe tener 10 dígitos (actual: ${this.value.length})`);
            }
        });
    }

    // 3. TELÉFONO ALTERNATIVO (OPCIONAL)
    const telefonoAltInput = document.getElementById('telefono_alternativo');
    if (telefonoAltInput) {
        telefonoAltInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 10) {
                value = value.slice(0, 10);
            }
            this.value = value;
        });
    }

    // 4. EMAIL - VALIDACIÓN BÁSICA
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const feedback = getOrCreateFeedback(this);
            const email = this.value;
            
            // Validación simple de email
            if (email.includes('@') && email.includes('.') && email.length > 5) {
                this.classList.add('valid');
                this.classList.remove('error');
                feedback.innerHTML = '<i class="fas fa-check-circle" style="color: #28a745;"></i> Email válido';
                feedback.style.color = '#28a745';
            } else if (email.length > 0) {
                this.classList.add('error');
                this.classList.remove('valid');
                feedback.innerHTML = '<i class="fas fa-exclamation-circle" style="color: #dc3545;"></i> Email inválido';
                feedback.style.color = '#dc3545';
            } else {
                this.classList.remove('valid', 'error');
                feedback.innerHTML = '';
            }
        });
    }

    // 5. NOMBRES Y APELLIDOS - SOLO LETRAS
    const nombreInput = document.getElementById('nombre');
    if (nombreInput) {
        nombreInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^a-zA-ZáéíóúñÑ\s]/g, '');
        });
    }

    const apellidosInput = document.getElementById('apellidos');
    if (apellidosInput) {
        apellidosInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^a-zA-ZáéíóúñÑ\s]/g, '');
        });
    }

    // 6. CONTRASEÑA - VALIDACIÓN EN TIEMPO REAL
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            validatePasswordStrength(this.value);
        });
    }

    // 7. CONFIRMAR CONTRASEÑA
    const confirmPasswordInput = document.getElementById('confirmar_password');
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            checkPasswordMatch();
        });
    }

    // ===== FUNCIONES DE VALIDACIÓN =====
    
    function validatePasswordStrength(password) {
        const strengthBar = document.querySelector('.strength-progress');
        if (!strengthBar) return;
        
        // Calcular fortaleza (0-100)
        let strength = 0;
        
        // Longitud (30%)
        if (password.length >= 6) strength += 30;
        else if (password.length >= 4) strength += 15;
        
        // Minúsculas (20%)
        if (/[a-z]/.test(password)) strength += 20;
        
        // Mayúsculas (20%)
        if (/[A-Z]/.test(password)) strength += 20;
        
        // Números (15%)
        if (/[0-9]/.test(password)) strength += 15;
        
        // Caracteres especiales (15%)
        if (/[^a-zA-Z0-9]/.test(password)) strength += 15;
        
        // Limitar a 100
        strength = Math.min(strength, 100);
        
        // Actualizar barra
        strengthBar.style.width = strength + '%';
        
        // Cambiar color
        if (strength < 40) {
            strengthBar.style.background = '#dc3545';
        } else if (strength < 70) {
            strengthBar.style.background = '#ffc107';
        } else {
            strengthBar.style.background = '#28a745';
        }
        
        // Actualizar requisitos
        updateRequirement('req-length', password.length >= 6);
        updateRequirement('req-lower', /[a-z]/.test(password));
        updateRequirement('req-upper', /[A-Z]/.test(password));
        updateRequirement('req-number', /[0-9]/.test(password));
        updateRequirement('req-special', /[^a-zA-Z0-9]/.test(password));
    }

    function updateRequirement(elementId, isValid) {
        const element = document.getElementById(elementId);
        if (element) {
            const icon = element.querySelector('i');
            if (isValid) {
                element.classList.add('valid');
                icon.className = 'fas fa-check-circle';
                icon.style.color = '#28a745';
            } else {
                element.classList.remove('valid');
                icon.className = 'far fa-circle';
                icon.style.color = '';
            }
        }
    }

    function checkPasswordMatch() {
        const password = document.getElementById('password')?.value || '';
        const confirm = document.getElementById('confirmar_password')?.value || '';
        const confirmField = document.getElementById('confirmar_password');
        
        if (!confirmField) return;
        
        const feedback = getOrCreateFeedback(confirmField);
        
        if (confirm && password === confirm) {
            confirmField.classList.add('valid');
            confirmField.classList.remove('error');
            feedback.innerHTML = '<i class="fas fa-check-circle" style="color: #28a745;"></i> Las contraseñas coinciden';
            feedback.style.color = '#28a745';
        } else if (confirm) {
            confirmField.classList.add('error');
            confirmField.classList.remove('valid');
            feedback.innerHTML = '<i class="fas fa-exclamation-circle" style="color: #dc3545;"></i> Las contraseñas no coinciden';
            feedback.style.color = '#dc3545';
        } else {
            confirmField.classList.remove('valid', 'error');
            feedback.innerHTML = '';
        }
    }

    // ===== FUNCIONES AUXILIARES =====
    
    function getOrCreateFeedback(input) {
        let feedback = input.parentNode.querySelector('.input-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'input-feedback';
            input.parentNode.appendChild(feedback);
        }
        return feedback;
    }

    function showFieldError(input, message) {
        const feedback = getOrCreateFeedback(input);
        input.classList.add('error');
        feedback.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        feedback.style.color = '#dc3545';
    }

    function showToast(message, type = 'info') {
        // Crear contenedor si no existe
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        // Crear toast
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        toast.innerHTML = `
            <i class="fas fa-${icons[type]}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        container.appendChild(toast);

        // Auto-eliminar
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    // ===== VALIDACIÓN DE PASOS =====
    
    function validateStep(step) {
        const stepElement = document.getElementById(`step${step}`);
        
        if (step === 1) {
            // Validar nombres
            const nombre = document.getElementById('nombre');
            if (!nombre.value.trim()) {
                showToast('Por favor, ingresa tus nombres', 'error');
                nombre.focus();
                return false;
            }
            if (nombre.value.length < 2) {
                showToast('Los nombres deben tener al menos 2 caracteres', 'error');
                nombre.focus();
                return false;
            }

            // Validar apellidos
            const apellidos = document.getElementById('apellidos');
            if (!apellidos.value.trim()) {
                showToast('Por favor, ingresa tus apellidos', 'error');
                apellidos.focus();
                return false;
            }
            if (apellidos.value.length < 2) {
                showToast('Los apellidos deben tener al menos 2 caracteres', 'error');
                apellidos.focus();
                return false;
            }

            // Validar cédula
            const cedula = document.getElementById('cedula');
            if (!cedula.value) {
                showToast('Por favor, ingresa tu cédula', 'error');
                cedula.focus();
                return false;
            }
            if (cedula.value.length !== 11) {
                showToast('La cédula debe tener 11 dígitos', 'error');
                cedula.focus();
                return false;
            }

            // Validar fecha de nacimiento
            const fechaNac = document.getElementById('fecha_nacimiento');
            if (!fechaNac.value) {
                showToast('Por favor, ingresa tu fecha de nacimiento', 'error');
                fechaNac.focus();
                return false;
            }
            
            // Validar edad (mayor de 18)
            const today = new Date();
            const birthDate = new Date(fechaNac.value);
            let age = today.getFullYear() - birthDate.getFullYear();
            const monthDiff = today.getMonth() - birthDate.getMonth();
            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
                age--;
            }
            if (age < 18) {
                showToast('Debes ser mayor de 18 años para registrarte', 'error');
                fechaNac.focus();
                return false;
            }
        }

        if (step === 2) {
            // Validar email
            const email = document.getElementById('email');
            if (!email.value) {
                showToast('Por favor, ingresa tu correo electrónico', 'error');
                email.focus();
                return false;
            }
            if (!email.value.includes('@') || !email.value.includes('.')) {
                showToast('Ingresa un correo electrónico válido', 'error');
                email.focus();
                return false;
            }

            // Validar teléfono
            const telefono = document.getElementById('telefono');
            if (!telefono.value) {
                showToast('Por favor, ingresa tu número de teléfono', 'error');
                telefono.focus();
                return false;
            }
            if (telefono.value.length !== 10) {
                showToast('El teléfono debe tener 10 dígitos', 'error');
                telefono.focus();
                return false;
            }
        }

        if (step === 3) {
            // Validar contraseña
            const password = document.getElementById('password');
            if (!password.value) {
                showToast('Por favor, ingresa una contraseña', 'error');
                password.focus();
                return false;
            }
            if (password.value.length < 6) {
                showToast('La contraseña debe tener al menos 6 caracteres', 'error');
                password.focus();
                return false;
            }

            // Validar confirmación
            const confirm = document.getElementById('confirmar_password');
            if (!confirm.value) {
                showToast('Por favor, confirma tu contraseña', 'error');
                confirm.focus();
                return false;
            }
            if (password.value !== confirm.value) {
                showToast('Las contraseñas no coinciden', 'error');
                confirm.focus();
                return false;
            }
        }

        if (step === 4) {
            // Validar términos
            const terminos = document.getElementById('terminos');
            if (!terminos.checked) {
                showToast('Debes aceptar los términos y condiciones', 'error');
                return false;
            }

            const privacidad = document.getElementById('privacidad');
            if (!privacidad.checked) {
                showToast('Debes aceptar la política de privacidad', 'error');
                return false;
            }

            const mayorEdad = document.getElementById('mayor_edad');
            if (!mayorEdad.checked) {
                showToast('Debes confirmar que eres mayor de 18 años', 'error');
                return false;
            }
        }

        return true;
    }

    // ===== NAVEGACIÓN ENTRE PASOS =====
    
    function updateNavigation() {
        // Actualizar botones
        if (prevBtn) prevBtn.disabled = currentStep === 1;
        
        if (currentStep === totalSteps) {
            if (nextBtn) nextBtn.style.display = 'none';
            if (submitBtn) submitBtn.style.display = 'flex';
        } else {
            if (nextBtn) nextBtn.style.display = 'flex';
            if (submitBtn) submitBtn.style.display = 'none';
        }

        // Actualizar pasos
        steps.forEach((step, index) => {
            step.classList.toggle('active', index + 1 === currentStep);
        });

        // Actualizar barra de progreso
        progressSteps.forEach((step, index) => {
            const stepNum = index + 1;
            step.classList.toggle('active', stepNum === currentStep);
            step.classList.toggle('completed', stepNum < currentStep);
        });

        // Scroll al inicio
        window.scrollTo({
            top: form.offsetTop - 100,
            behavior: 'smooth'
        });
    }

    // Event listeners para navegación
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (validateStep(currentStep)) {
                if (currentStep < totalSteps) {
                    currentStep++;
                    updateNavigation();
                }
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (currentStep > 1) {
                currentStep--;
                updateNavigation();
            }
        });
    }

    // Envío del formulario
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Validar todos los pasos
            for (let step = 1; step <= totalSteps; step++) {
                if (!validateStep(step)) {
                    currentStep = step;
                    updateNavigation();
                    return;
                }
            }

            // Mostrar éxito
            showToast('¡Registro exitoso! Redirigiendo...', 'success');
            
            // Simular envío
            setTimeout(() => {
                window.location.href = '/login?registered=true';
            }, 2000);
        });
    }

    // Inicializar navegación
    updateNavigation();
}

// Agregar estilos necesarios
const styles = `
    .toast-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
    }

    .toast {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 300px;
        border-left: 4px solid;
        animation: slideIn 0.3s ease;
    }

    .toast.success {
        border-left-color: #28a745;
    }

    .toast.success i {
        color: #28a745;
    }

    .toast.error {
        border-left-color: #dc3545;
    }

    .toast.error i {
        color: #dc3545;
    }

    .toast.warning {
        border-left-color: #ffc107;
    }

    .toast.warning i {
        color: #ffc107;
    }

    .toast.info {
        border-left-color: #17a2b8;
    }

    .toast.info i {
        color: #17a2b8;
    }

    .toast-close {
        margin-left: auto;
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

    .input-feedback {
        margin-top: 0.3rem;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }

    input.valid {
        border-color: #28a745 !important;
    }

    input.error {
        border-color: #dc3545 !important;
    }

    .strength-requirements li.valid {
        color: #28a745;
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

    @media (max-width: 768px) {
        .toast {
            min-width: auto;
            width: calc(100vw - 40px);
        }
    }
`;


const telefono = document.getElementById("telefono");

telefono.addEventListener("input", function () {
    this.value = this.value.replace(/\D/g, "").slice(0,10);
});

// Agregar estilos al documento
const styleSheet = document.createElement('style');
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);