// configuracion.js - Manejo completo de la configuración

let configActual = CONFIG_INICIAL || {};

// Función para guardar una sección completa
async function guardarSeccion(seccion) {
    const datos = {};
    const toast = document.getElementById('toast');
    
    // Mapeo de IDs de inputs a claves de configuración
    const mapeoCampos = {
        general: {
            'cfg_nombre_municipio': 'nombre_municipio',
            'cfg_siglas': 'siglas',
            'cfg_direccion': 'direccion',
            'cfg_telefono': 'telefono',
            'cfg_email': 'email_institucional',
            'cfg_web': 'sitio_web',
            'cfg_timezone': 'zona_horaria',
            'cfg_date_format': 'formato_fecha',
            'cfg_idioma': 'idioma'
        },
        seguridad: {
            'cfg_pass_min': 'pass_min_length',
            'cfg_max_intentos': 'max_intentos_fallidos',
            'cfg_pass_expiry': 'pass_expiry_dias',
            'cfg_lockout_time': 'lockout_minutos',
            'cfg_session_hours': 'session_duracion_horas',
            'cfg_inactivity': 'inactividad_minutos',
            'cfg_require_upper': 'require_mayusculas',
            'cfg_require_num': 'require_numeros',
            'cfg_require_special': 'require_especiales',
            'cfg_single_session': 'single_session',
            'cfg_log_access': 'log_intentos_acceso',
            'cfg_2fa': 'two_factor_auth'
        },
        notificaciones: {
            'cfg_smtp_host': 'smtp_host',
            'cfg_smtp_port': 'smtp_port',
            'cfg_smtp_user': 'smtp_user',
            'cfg_smtp_pass': 'smtp_password',
            'cfg_smtp_name': 'smtp_name',
            'cfg_notif_solicitud': 'notif_nueva_solicitud',
            'cfg_notif_denuncia': 'notif_nueva_denuncia',
            'cfg_notif_usuario': 'notif_nuevo_usuario',
            'cfg_notif_estado': 'notif_cambio_estado',
            'cfg_notif_resumen': 'notif_resumen_diario'
        },
        servicios: {
            'cfg_max_solicitudes': 'max_solicitudes_mes',
            'cfg_max_denuncias': 'max_denuncias_mes',
            'cfg_max_file_size': 'max_file_size_mb',
            'cfg_file_types': 'tipos_archivo_permitidos'
        },
        apariencia: {
            'cfg_color_primary': 'color_primario',
            'cfg_color_primary_hex': 'color_primario_hex',
            'cfg_color_accent': 'color_acento',
            'cfg_color_accent_hex': 'color_acento_hex',
            'cfg_color_sidebar': 'color_sidebar',
            'cfg_color_sidebar_hex': 'color_sidebar_hex',
            'cfg_sidebar_collapsed': 'sidebar_colapsado',
            'cfg_breadcrumbs': 'mostrar_breadcrumbs',
            'cfg_animations': 'animaciones'
        },
        sistema: {
            'cfg_debug': 'debug_mode',
            'cfg_maintenance': 'maintenance_mode',
            'cfg_audit_log': 'audit_log',
            'cfg_file_log': 'file_logging',
            'cfg_cache_sessions': 'cache_sessions_segundos',
            'cfg_cache_static': 'cache_static_dias'
        }
    };
    
    // Recoger valores según la sección
    const campos = mapeoCampos[seccion];
    if (campos) {
        for (const [inputId, configKey] of Object.entries(campos)) {
            const elemento = document.getElementById(inputId);
            if (elemento) {
                if (elemento.type === 'checkbox') {
                    datos[configKey] = elemento.checked;
                } else if (elemento.type === 'number') {
                    datos[configKey] = parseInt(elemento.value) || 0;
                } else {
                    datos[configKey] = elemento.value;
                }
            }
        }
    }
    
    // Servicios específicos (tiempos de respuesta)
    if (seccion === 'servicios') {
        const tiempos = {};
        document.querySelectorAll('.svc-tiempo').forEach(input => {
            const key = input.dataset.key;
            tiempos[key] = parseInt(input.value) || 0;
        });
        datos['tiempos_respuesta'] = tiempos;
        
        const activos = {};
        document.querySelectorAll('.svc-activo').forEach(checkbox => {
            const key = checkbox.dataset.key;
            activos[key] = checkbox.checked;
        });
        datos['servicios_activos'] = activos;
    }
    
    if (Object.keys(datos).length === 0) {
        mostrarToast('No hay datos para guardar', 'warning');
        return;
    }
    
    mostrarToast('Guardando configuración...', 'info');
    
    try {
        const response = await fetch('/admin/api/config/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seccion: seccion, datos: datos })
        });
        
        const result = await response.json();
        
        if (result.ok) {
            mostrarToast(result.mensaje || '✅ Configuración guardada correctamente', 'success');
            // Aplicar cambios visuales inmediatos
            aplicarCambiosVisuales(seccion, datos);
        } else {
            mostrarToast('❌ Error: ' + (result.error || 'No se pudo guardar'), 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarToast('❌ Error de conexión al guardar', 'error');
    }
}

// Función para aplicar cambios visuales inmediatos
function aplicarCambiosVisuales(seccion, datos) {
    if (seccion === 'apariencia') {
        if (datos.color_primario) {
            document.documentElement.style.setProperty('--primary-color', datos.color_primario);
        }
        if (datos.color_acento) {
            document.documentElement.style.setProperty('--accent-color', datos.color_acento);
        }
        if (datos.color_sidebar) {
            document.documentElement.style.setProperty('--sidebar-bg', datos.color_sidebar);
        }
    }
    
    if (seccion === 'sistema') {
        if (datos.maintenance_mode) {
            mostrarToast('⚠️ Modo mantenimiento activado', 'warning');
        }
    }
}

// Función para reiniciar una sección a valores por defecto
function resetSeccion(seccion) {
    if (confirm('¿Restablecer esta sección a valores por defecto?')) {
        // Recargar valores desde la configuración inicial
        cargarConfiguracionInicial();
        mostrarToast('Configuración restablecida', 'info');
    }
}

// Función para cargar configuración inicial
function cargarConfiguracionInicial() {
    if (CONFIG_INICIAL) {
        for (const [key, value] of Object.entries(CONFIG_INICIAL)) {
            const elemento = document.getElementById(`cfg_${key}`);
            if (elemento) {
                if (elemento.type === 'checkbox') {
                    elemento.checked = value === true || value === 'true';
                } else if (elemento.type === 'number') {
                    elemento.value = value || 0;
                } else {
                    elemento.value = value || '';
                }
            }
        }
    }
}

// Función para probar SMTP
async function testSmtp() {
    const testEmail = document.getElementById('cfg_test_email').value;
    if (!testEmail) {
        mostrarToast('Ingresa un email para enviar la prueba', 'warning');
        return;
    }
    
    const smtpConfig = {
        smtp_host: document.getElementById('cfg_smtp_host').value,
        smtp_port: parseInt(document.getElementById('cfg_smtp_port').value) || 587,
        smtp_user: document.getElementById('cfg_smtp_user').value,
        smtp_pass: document.getElementById('cfg_smtp_pass').value,
        smtp_name: document.getElementById('cfg_smtp_name').value,
        email_destino: testEmail
    };
    
    const resultDiv = document.getElementById('smtpTestResult');
    resultDiv.className = 'test-result';
    resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando prueba...';
    resultDiv.classList.remove('hidden');
    
    try {
        const response = await fetch('/admin/api/config/test-smtp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(smtpConfig)
        });
        
        const result = await response.json();
        
        if (result.ok) {
            resultDiv.className = 'test-result success';
            resultDiv.innerHTML = '<i class="fas fa-check-circle"></i> ' + (result.msg || 'Email de prueba enviado correctamente');
        } else {
            resultDiv.className = 'test-result error';
            resultDiv.innerHTML = '<i class="fas fa-times-circle"></i> ' + (result.msg || 'Error al enviar email');
        }
    } catch (error) {
        resultDiv.className = 'test-result error';
        resultDiv.innerHTML = '<i class="fas fa-times-circle"></i> Error de conexión';
    }
}

// Función para limpiar caché
async function limpiarCache() {
    mostrarToast('Limpiando caché...', 'info');
    
    try {
        const response = await fetch('/admin/api/config/limpiar-cache', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.ok) {
            mostrarToast(result.msg || '✅ Caché limpiada correctamente', 'success');
        } else {
            mostrarToast('❌ Error: ' + (result.msg || 'No se pudo limpiar la caché'), 'error');
        }
    } catch (error) {
        mostrarToast('❌ Error de conexión', 'error');
    }
}

// Función para exportar datos
async function exportarDatos() {
    mostrarToast('Generando exportación...', 'info');
    
    try {
        window.location.href = '/admin/api/config/exportar';
        mostrarToast('✅ Exportación iniciada', 'success');
    } catch (error) {
        mostrarToast('❌ Error al exportar', 'error');
    }
}

// Función para mostrar notificaciones toast
function mostrarToast(mensaje, tipo = 'success') {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastMsg = document.getElementById('toastMsg');
    
    toastIcon.className = tipo === 'success' ? 'fas fa-check-circle' : 
                          tipo === 'error' ? 'fas fa-times-circle' : 
                          tipo === 'warning' ? 'fas fa-exclamation-triangle' : 'fas fa-info-circle';
    
    toastMsg.textContent = mensaje;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Función para confirmar reinicio
function confirmarReset() {
    const modal = document.getElementById('confirmModal');
    const confirmBtn = document.getElementById('confirmBtn');
    const confirmMsg = document.getElementById('confirmMsg');
    
    confirmMsg.innerHTML = '⚠️ Esta acción eliminará TODOS los datos del sistema. <strong>No se puede deshacer.</strong><br><br>¿Estás completamente seguro?';
    modal.classList.add('show');
    
    const handler = async () => {
        confirmBtn.removeEventListener('click', handler);
        modal.classList.remove('show');
        
        mostrarToast('Reiniciando datos...', 'info');
        
        try {
            const response = await fetch('/admin/api/config/reset-datos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.ok) {
                mostrarToast('✅ Datos reiniciados correctamente', 'success');
                setTimeout(() => location.reload(), 2000);
            } else {
                mostrarToast('❌ Error: ' + (result.error || 'No se pudo reiniciar'), 'error');
            }
        } catch (error) {
            mostrarToast('❌ Error de conexión', 'error');
        }
    };
    
    confirmBtn.onclick = handler;
}

function closeModal() {
    document.getElementById('confirmModal').classList.remove('show');
}

// Función para alternar visibilidad de contraseña
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    
    if (input.type === 'password') {
        input.type = 'text';
        button.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        input.type = 'password';
        button.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

// Función para copiar texto
function copyText(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        mostrarToast('✅ Copiado al portapapeles', 'success');
    }).catch(() => {
        mostrarToast('❌ No se pudo copiar', 'error');
    });
}

// Función para seleccionar motor de BD
function selectEngine(engine) {
    document.querySelectorAll('.db-engine-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelector(`.db-engine-card[data-engine="${engine}"]`).classList.add('active');
    
    document.querySelectorAll('.db-config-panel').forEach(panel => {
        panel.classList.add('hidden');
    });
    
    if (engine === 'sqlite') {
        document.getElementById('db-sqlite-config').classList.remove('hidden');
        updateSqliteUrl();
    } else if (engine === 'postgresql') {
        document.getElementById('db-postgresql-config').classList.remove('hidden');
        updatePostgresUrl();
    } else if (engine === 'mysql') {
        document.getElementById('db-mysql-config').classList.remove('hidden');
        updateMysqlUrl();
    }
}

// Actualizar URLs de base de datos
function updateSqliteUrl() {
    const path = document.getElementById('cfg_sqlite_path').value;
    const url = `sqlite:///${path}`;
    document.getElementById('sqlite-url').textContent = url;
}

function updatePostgresUrl() {
    const host = document.getElementById('cfg_pg_host').value;
    const port = document.getElementById('cfg_pg_port').value;
    const db = document.getElementById('cfg_pg_db').value;
    const user = document.getElementById('cfg_pg_user').value;
    const pass = document.getElementById('cfg_pg_pass').value;
    const url = `postgresql://${user}:${pass}@${host}:${port}/${db}`;
    document.getElementById('pg-url').textContent = url;
}

function updateMysqlUrl() {
    const host = document.getElementById('cfg_my_host').value;
    const port = document.getElementById('cfg_my_port').value;
    const db = document.getElementById('cfg_my_db').value;
    const user = document.getElementById('cfg_my_user').value;
    const pass = document.getElementById('cfg_my_pass').value;
    const url = `mysql+pymysql://${user}:${pass}@${host}:${port}/${db}`;
    document.getElementById('my-url').textContent = url;
}

// Función para seleccionar tema
function selectTheme(theme) {
    document.querySelectorAll('.theme-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelector(`.theme-card[data-theme="${theme}"]`).classList.add('active');
    
    const themes = {
        default: { primary: '#2d6a4f', accent: '#e9c46a', sidebar: '#1b4332' },
        dark: { primary: '#1a1a2e', accent: '#e94560', sidebar: '#0f3460' },
        blue: { primary: '#1e3a5f', accent: '#89c2d9', sidebar: '#0b2545' }
    };
    
    const colors = themes[theme];
    if (colors) {
        document.getElementById('cfg_color_primary').value = colors.primary;
        document.getElementById('cfg_color_primary_hex').value = colors.primary;
        document.getElementById('cfg_color_accent').value = colors.accent;
        document.getElementById('cfg_color_accent_hex').value = colors.accent;
        document.getElementById('cfg_color_sidebar').value = colors.sidebar;
        document.getElementById('cfg_color_sidebar_hex').value = colors.sidebar;
        
        // Aplicar visualmente
        document.documentElement.style.setProperty('--primary-color', colors.primary);
        document.documentElement.style.setProperty('--accent-color', colors.accent);
        document.documentElement.style.setProperty('--sidebar-bg', colors.sidebar);
    }
}

// Cargar información del sistema
async function cargarInfoSistema() {
    try {
        const response = await fetch('/admin/api/config/sistema-info');
        const result = await response.json();
        
        if (result.ok) {
            document.getElementById('sys-python').textContent = result.datos.python_version || 'N/A';
            document.getElementById('sys-flask').textContent = result.datos.flask_version || 'N/A';
        }
    } catch (error) {
        console.error('Error cargando info sistema:', error);
    }
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔧 Inicializando configuración...');
    
    // Cargar info del sistema
    cargarInfoSistema();
    
    // Configurar listeners para URLs de BD
    const sqlitePath = document.getElementById('cfg_sqlite_path');
    if (sqlitePath) sqlitePath.addEventListener('input', updateSqliteUrl);
    
    const pgInputs = ['cfg_pg_host', 'cfg_pg_port', 'cfg_pg_db', 'cfg_pg_user', 'cfg_pg_pass'];
    pgInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) input.addEventListener('input', updatePostgresUrl);
    });
    
    const myInputs = ['cfg_my_host', 'cfg_my_port', 'cfg_my_db', 'cfg_my_user', 'cfg_my_pass'];
    myInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) input.addEventListener('input', updateMysqlUrl);
    });
    
    // Sincronizar color picker con input text
    const colorPrimary = document.getElementById('cfg_color_primary');
    const colorPrimaryHex = document.getElementById('cfg_color_primary_hex');
    if (colorPrimary && colorPrimaryHex) {
        colorPrimary.addEventListener('input', () => colorPrimaryHex.value = colorPrimary.value);
        colorPrimaryHex.addEventListener('input', () => colorPrimary.value = colorPrimaryHex.value);
    }
    
    const colorAccent = document.getElementById('cfg_color_accent');
    const colorAccentHex = document.getElementById('cfg_color_accent_hex');
    if (colorAccent && colorAccentHex) {
        colorAccent.addEventListener('input', () => colorAccentHex.value = colorAccent.value);
        colorAccentHex.addEventListener('input', () => colorAccent.value = colorAccentHex.value);
    }
    
    const colorSidebar = document.getElementById('cfg_color_sidebar');
    const colorSidebarHex = document.getElementById('cfg_color_sidebar_hex');
    if (colorSidebar && colorSidebarHex) {
        colorSidebar.addEventListener('input', () => colorSidebarHex.value = colorSidebar.value);
        colorSidebarHex.addEventListener('input', () => colorSidebar.value = colorSidebarHex.value);
    }
    
    // Navegación entre secciones
    document.querySelectorAll('.config-nav-item').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.dataset.section;
            
            document.querySelectorAll('.config-nav-item').forEach(item => item.classList.remove('active'));
            link.classList.add('active');
            
            document.querySelectorAll('.config-section').forEach(sec => sec.classList.remove('active'));
            document.getElementById(`seccion-${section}`).classList.add('active');
        });
    });
    
    console.log('✅ Configuración inicializada correctamente');
});