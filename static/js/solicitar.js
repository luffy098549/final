/**
 * solicitar.js - Validación y funcionalidades para formularios de solicitud
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    const form = document.querySelector('form');
    const inputs = document.querySelectorAll('input[required], textarea[required]');
    
    // ===================================================
    // 1. VALIDACIÓN DEL FORMULARIO
    // ===================================================
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            let firstError = null;
            
            // Validar campos requeridos
            inputs.forEach(input => {
                const value = input.value.trim();
                const errorElement = input.nextElementSibling;
                
                // Remover errores previos
                if (errorElement && errorElement.classList.contains('error-message')) {
                    errorElement.remove();
                }
                input.classList.remove('error');
                
                if (!value) {
                    isValid = false;
                    input.classList.add('error');
                    
                    // Crear mensaje de error
                    const error = document.createElement('span');
                    error.className = 'error-message';
                    error.textContent = 'Este campo es requerido';
                    error.style.color = '#dc3545';
                    error.style.fontSize = '0.875rem';
                    error.style.marginTop = '5px';
                    error.style.display = 'block';
                    
                    input.parentNode.insertBefore(error, input.nextSibling);
                    
                    if (!firstError) {
                        firstError = input;
                    }
                }
                
                // Validaciones específicas
                if (value) {
                    // Validar cédula dominicana (formato simple)
                    if (input.id === 'cedula') {
                        const cedulaRegex = /^\d{3}-\d{7}-\d{1}$|^\d{11}$/;
                        if (!cedulaRegex.test(value.replace(/-/g, ''))) {
                            isValid = false;
                            input.classList.add('error');
                            mostrarError(input, 'Ingrese una cédula válida (000-0000000-0)');
                        }
                    }
                    
                    // Validar teléfono
                    if (input.id === 'telefono') {
                        const telefonoRegex = /^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/;
                        if (!telefonoRegex.test(value)) {
                            isValid = false;
                            input.classList.add('error');
                            mostrarError(input, 'Ingrese un teléfono válido');
                        }
                    }
                    
                    // Validar email
                    if (input.id === 'email' && value) {
                        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                        if (!emailRegex.test(value)) {
                            isValid = false;
                            input.classList.add('error');
                            mostrarError(input, 'Ingrese un email válido');
                        }
                    }
                }
            });
            
            // Validar términos y condiciones
            const terminos = document.querySelector('input[name="terminos"]');
            if (terminos && !terminos.checked) {
                isValid = false;
                terminos.classList.add('error');
                alert('Debe aceptar los términos y condiciones');
            }
            
            if (!isValid) {
                e.preventDefault();
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            } else {
                // Mostrar indicador de carga
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = 'Enviando... <span class="spinner"></span>';
                }
            }
        });
    }
    
    // Función auxiliar para mostrar errores
    function mostrarError(input, mensaje) {
        const error = document.createElement('span');
        error.className = 'error-message';
        error.textContent = mensaje;
        error.style.color = '#dc3545';
        error.style.fontSize = '0.875rem';
        error.style.marginTop = '5px';
        error.style.display = 'block';
        
        // Remover error previo si existe
        const prevError = input.nextElementSibling;
        if (prevError && prevError.classList.contains('error-message')) {
            prevError.remove();
        }
        
        input.parentNode.insertBefore(error, input.nextSibling);
    }
    
    // ===================================================
    // 2. MÁSCARAS PARA INPUTS
    // ===================================================
    const cedulaInput = document.getElementById('cedula');
    if (cedulaInput) {
        cedulaInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 3) {
                value = value.substring(0, 3) + '-' + value.substring(3);
            }
            if (value.length > 11) {
                value = value.substring(0, 11) + '-' + value.substring(11, 12);
            }
            this.value = value.substring(0, 13); // 000-0000000-0
        });
    }
    
    const telefonoInput = document.getElementById('telefono');
    if (telefonoInput) {
        telefonoInput.addEventListener('input', function(e) {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 0) {
                if (value.length <= 3) {
                    value = '(' + value;
                } else if (value.length <= 6) {
                    value = '(' + value.substring(0, 3) + ') ' + value.substring(3);
                } else {
                    value = '(' + value.substring(0, 3) + ') ' + value.substring(3, 6) + '-' + value.substring(6, 10);
                }
            }
            this.value = value;
        });
    }
    
    // ===================================================
    // 3. AUTOCOMPLETADO DEL USUARIO (si está logueado)
    // ===================================================
    // Esto asume que tienes una variable con datos del usuario
    if (typeof usuario !== 'undefined' && usuario) {
        const nombreInput = document.getElementById('nombre');
        const cedulaInput = document.getElementById('cedula');
        const emailInput = document.getElementById('email');
        const telefonoInput = document.getElementById('telefono');
        
        if (nombreInput && usuario.nombre) nombreInput.value = usuario.nombre;
        if (cedulaInput && usuario.cedula) cedulaInput.value = usuario.cedula;
        if (emailInput && usuario.email) emailInput.value = usuario.email;
        if (telefonoInput && usuario.telefono) telefonoInput.value = usuario.telefono;
    }
    
    // ===================================================
    // 4. CONFIRMAR CANCELACIÓN
    // ===================================================
    const cancelBtn = document.querySelector('.btn-secondary');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            if (form && form.querySelector('input:not([type="checkbox"]):not([value=""]), textarea:not(:empty)')) {
                if (!confirm('¿Está seguro de cancelar? Los datos ingresados se perderán.')) {
                    e.preventDefault();
                }
            }
        });
    }
});

// Añadir estilos para errores y spinner
const style = document.createElement('style');
style.textContent = `
    input.error, textarea.error {
        border-color: #dc3545 !important;
        background-color: #fff8f8;
    }
    
    .spinner {
        display: inline-block;
        width: 1rem;
        height: 1rem;
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 0.8s linear infinite;
        margin-left: 8px;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    button:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
`;
document.head.appendChild(style);