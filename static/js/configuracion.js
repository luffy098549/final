/* ================================================================
   configuracion.js — Lógica completa y funcional
   Todos los fetch() apuntan a rutas reales de Flask
================================================================ */
'use strict';

// ================================================================
// INICIALIZACIÓN
// ================================================================

document.addEventListener('DOMContentLoaded', function () {
    initNavigation();
    precargarFormularios();
    initUploadZones();
    initColorInputs();
    initDBListeners();
    cargarInfoSistema();
});

// ================================================================
// NAVEGACIÓN ENTRE SECCIONES
// ================================================================

function initNavigation() {
    document.querySelectorAll('.config-nav-item').forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            cambiarSeccion(this.dataset.section);
        });
    });
}

function cambiarSeccion(seccion) {
    document.querySelectorAll('.config-nav-item').forEach(i => i.classList.remove('active'));
    document.querySelectorAll('.config-section').forEach(s => s.classList.remove('active'));

    document.querySelector(`[data-section="${seccion}"]`)?.classList.add('active');
    document.getElementById(`seccion-${seccion}`)?.classList.add('active');
}

// ================================================================
// PRECARGAR FORMULARIOS CON CONFIG_INICIAL (desde Flask)
// ================================================================

function precargarFormularios() {
    if (typeof CONFIG_INICIAL === 'undefined') return;

    // ── General ──
    const g = CONFIG_INICIAL.general || {};
    setVal('cfg_nombre_municipio', g.nombre_municipio);
    setVal('cfg_siglas',           g.siglas);
    setVal('cfg_direccion',        g.direccion);
    setVal('cfg_telefono',         g.telefono);
    setVal('cfg_email',            g.email);
    setVal('cfg_web',              g.web);
    setVal('cfg_timezone',         g.timezone);
    setVal('cfg_date_format',      g.date_format);
    setVal('cfg_idioma',           g.idioma);

    // ── Seguridad ──
    const s = CONFIG_INICIAL.seguridad || {};
    setVal('cfg_pass_min',       s.pass_min);
    setVal('cfg_max_intentos',   s.max_intentos);
    setVal('cfg_pass_expiry',    s.pass_expiry);
    setVal('cfg_lockout_time',   s.lockout_time);
    setVal('cfg_session_hours',  s.session_hours);
    setVal('cfg_inactivity',     s.inactivity);
    setCheck('cfg_require_upper',   s.require_upper);
    setCheck('cfg_require_num',     s.require_num);
    setCheck('cfg_require_special', s.require_special);
    setCheck('cfg_single_session',  s.single_session);
    setCheck('cfg_log_access',      s.log_access);

    // ── Notificaciones ──
    const n = CONFIG_INICIAL.notificaciones || {};
    setVal('cfg_smtp_host',  n.smtp_host);
    setVal('cfg_smtp_port',  n.smtp_port);
    setVal('cfg_smtp_user',  n.smtp_user);
    setVal('cfg_smtp_pass',  n.smtp_pass);
    setVal('cfg_smtp_name',  n.smtp_name);
    setCheck('cfg_notif_solicitud', n.notif_solicitud);
    setCheck('cfg_notif_denuncia',  n.notif_denuncia);
    setCheck('cfg_notif_usuario',   n.notif_usuario);
    setCheck('cfg_notif_estado',    n.notif_estado);

    // ── Servicios ──
    const svc = CONFIG_INICIAL.servicios || {};
    const tiempos = svc.tiempos || {};
    const activos = svc.activos || {};

    document.querySelectorAll('.svc-tiempo').forEach(input => {
        const key = input.dataset.key;
        if (tiempos[key] !== undefined) input.value = tiempos[key];
    });
    document.querySelectorAll('.svc-activo').forEach(cb => {
        const key = cb.dataset.key;
        if (activos[key] !== undefined) cb.checked = activos[key];
    });

    setVal('cfg_max_solicitudes', svc.max_solicitudes);
    setVal('cfg_max_denuncias',   svc.max_denuncias);
    setVal('cfg_max_file_size',   svc.max_file_size);
    setVal('cfg_file_types',      svc.file_types);

    // ── Apariencia ──
    const a = CONFIG_INICIAL.apariencia || {};
    selectTheme(a.tema || 'default', false); // false = no guardar, solo visual
    setVal('cfg_color_primary',     a.color_primary);
    setVal('cfg_color_primary_hex', a.color_primary);
    setVal('cfg_color_accent',      a.color_accent);
    setVal('cfg_color_accent_hex',  a.color_accent);
    setVal('cfg_color_sidebar',     a.color_sidebar);
    setVal('cfg_color_sidebar_hex', a.color_sidebar);
    setCheck('cfg_sidebar_collapsed', a.sidebar_collapsed);
    setCheck('cfg_breadcrumbs',       a.breadcrumbs);
    setCheck('cfg_animations',        a.animations);

    // ── Sistema ──
    const sis = CONFIG_INICIAL.sistema || {};
    setCheck('cfg_debug',       sis.debug);
    setCheck('cfg_maintenance', sis.maintenance);
    setCheck('cfg_audit_log',   sis.audit_log);
    setCheck('cfg_file_log',    sis.file_log);
    setVal('cfg_cache_sessions', sis.cache_sessions);
    setVal('cfg_cache_static',   sis.cache_static);
}

// Helpers de precarga
function setVal(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.value = val;
}
function setCheck(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.checked = Boolean(val);
}

// ================================================================
// GUARDAR SECCIÓN — fetch real a Flask
// ================================================================

async function guardarSeccion(seccion) {
    const datos = recopilarDatos(seccion);
    const btn   = document.querySelector(`#seccion-${seccion} .btn-save`);

    if (btn) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        btn.disabled  = true;
    }

    try {
        const res = await fetch('/admin/api/config/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seccion, datos })
        });
        const json = await res.json();

        if (json.ok) {
            mostrarToast(json.msg, 'success');
            // Si es mantenimiento, notificar en tiempo real
            if (seccion === 'sistema' && datos.maintenance !== undefined) {
                await fetch('/admin/api/config/mantenimiento', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ activo: datos.maintenance })
                });
            }
        } else {
            mostrarToast(json.msg || 'Error al guardar', 'error');
        }
    } catch (err) {
        mostrarToast('Error de conexión: ' + err.message, 'error');
    } finally {
        if (btn) {
            btn.innerHTML = '<i class="fas fa-save"></i> Guardar Cambios';
            btn.disabled  = false;
        }
    }
}

// ── Recopilar datos de una sección ──────────────────────────
function recopilarDatos(seccion) {
    const datos = {};

    if (seccion === 'general') {
        datos.nombre_municipio = getVal('cfg_nombre_municipio');
        datos.siglas           = getVal('cfg_siglas');
        datos.direccion        = getVal('cfg_direccion');
        datos.telefono         = getVal('cfg_telefono');
        datos.email            = getVal('cfg_email');
        datos.web              = getVal('cfg_web');
        datos.timezone         = getVal('cfg_timezone');
        datos.date_format      = getVal('cfg_date_format');
        datos.idioma           = getVal('cfg_idioma');
    }
    else if (seccion === 'seguridad') {
        datos.pass_min       = getNum('cfg_pass_min');
        datos.max_intentos   = getNum('cfg_max_intentos');
        datos.pass_expiry    = getNum('cfg_pass_expiry');
        datos.lockout_time   = getNum('cfg_lockout_time');
        datos.session_hours  = getNum('cfg_session_hours');
        datos.inactivity     = getNum('cfg_inactivity');
        datos.require_upper   = getCheck('cfg_require_upper');
        datos.require_num     = getCheck('cfg_require_num');
        datos.require_special = getCheck('cfg_require_special');
        datos.single_session  = getCheck('cfg_single_session');
        datos.log_access      = getCheck('cfg_log_access');
    }
    else if (seccion === 'notificaciones') {
        datos.smtp_host      = getVal('cfg_smtp_host');
        datos.smtp_port      = getNum('cfg_smtp_port');
        datos.smtp_user      = getVal('cfg_smtp_user');
        datos.smtp_pass      = getVal('cfg_smtp_pass');
        datos.smtp_name      = getVal('cfg_smtp_name');
        datos.notif_solicitud = getCheck('cfg_notif_solicitud');
        datos.notif_denuncia  = getCheck('cfg_notif_denuncia');
        datos.notif_usuario   = getCheck('cfg_notif_usuario');
        datos.notif_estado    = getCheck('cfg_notif_estado');
    }
    else if (seccion === 'servicios') {
        datos.tiempos = {};
        datos.activos = {};
        document.querySelectorAll('.svc-tiempo').forEach(el => {
            datos.tiempos[el.dataset.key] = parseInt(el.value) || 1;
        });
        document.querySelectorAll('.svc-activo').forEach(el => {
            datos.activos[el.dataset.key] = el.checked;
        });
        datos.max_solicitudes = getNum('cfg_max_solicitudes');
        datos.max_denuncias   = getNum('cfg_max_denuncias');
        datos.max_file_size   = getNum('cfg_max_file_size');
        datos.file_types      = getVal('cfg_file_types');
    }
    else if (seccion === 'apariencia') {
        datos.tema             = document.querySelector('.theme-card.active')?.dataset.theme || 'default';
        datos.color_primary    = getVal('cfg_color_primary');
        datos.color_accent     = getVal('cfg_color_accent');
        datos.color_sidebar    = getVal('cfg_color_sidebar');
        datos.sidebar_collapsed = getCheck('cfg_sidebar_collapsed');
        datos.breadcrumbs      = getCheck('cfg_breadcrumbs');
        datos.animations       = getCheck('cfg_animations');
    }
    else if (seccion === 'sistema') {
        datos.debug         = getCheck('cfg_debug');
        datos.maintenance   = getCheck('cfg_maintenance');
        datos.audit_log     = getCheck('cfg_audit_log');
        datos.file_log      = getCheck('cfg_file_log');
        datos.cache_sessions = getNum('cfg_cache_sessions');
        datos.cache_static   = getNum('cfg_cache_static');
    }

    return datos;
}

function getVal(id)   { return document.getElementById(id)?.value?.trim() || ''; }
function getNum(id)   { return parseInt(document.getElementById(id)?.value) || 0; }
function getCheck(id) { return document.getElementById(id)?.checked || false; }

// ── Restablecer sección ──────────────────────────────────────
function resetSeccion(seccion) {
    mostrarConfirm(
        'Restablecer sección',
        `¿Restablecer "${seccion}" a los valores por defecto?`,
        () => location.reload()
    );
}

// ================================================================
// UPLOAD DE IMÁGENES — fetch real a Flask
// ================================================================

function initUploadZones() {
    [
        { zona: 'uploadLogo',    input: 'inputLogo',    tipo: 'logo' },
        { zona: 'uploadFavicon', input: 'inputFavicon', tipo: 'favicon' },
        { zona: 'uploadBanner',  input: 'inputBanner',  tipo: 'banner' },
    ].forEach(({ zona, input, tipo }) => {
        const zEl = document.getElementById(zona);
        const iEl = document.getElementById(input);
        if (!zEl || !iEl) return;

        zEl.addEventListener('click', () => iEl.click());

        zEl.addEventListener('dragover', e => {
            e.preventDefault();
            zEl.style.borderColor = '#7E8F76';
            zEl.style.background  = '#f0f7f0';
        });
        zEl.addEventListener('dragleave', () => {
            zEl.style.borderColor = '';
            zEl.style.background  = '';
        });
        zEl.addEventListener('drop', e => {
            e.preventDefault();
            zEl.style.borderColor = '';
            zEl.style.background  = '';
            if (e.dataTransfer.files[0]) subirImagen(zEl, e.dataTransfer.files[0], tipo);
        });

        iEl.addEventListener('change', () => {
            if (iEl.files[0]) subirImagen(zEl, iEl.files[0], tipo);
        });
    });
}

async function subirImagen(zona, archivo, tipo) {
    // Preview inmediato
    const reader = new FileReader();
    reader.onload = e => {
        zona.innerHTML = `
            <img src="${e.target.result}" style="max-height:60px;border-radius:6px;object-fit:contain;">
            <p style="margin:6px 0 0;font-size:0.75rem;color:#D97706;font-weight:600;">
                <i class="fas fa-spinner fa-spin"></i> Subiendo...
            </p>`;
    };
    reader.readAsDataURL(archivo);

    // Subir al servidor
    const formData = new FormData();
    formData.append('tipo', tipo);
    formData.append('archivo', archivo);

    try {
        const res  = await fetch('/admin/api/config/subir-imagen', { method: 'POST', body: formData });
        const json = await res.json();

        if (json.ok) {
            zona.querySelector('p').innerHTML = `<i class="fas fa-check"></i> ${archivo.name}`;
            zona.querySelector('p').style.color = '#38a169';
            mostrarToast(json.msg, 'success');
        } else {
            zona.querySelector('p').innerHTML = `<i class="fas fa-times"></i> Error: ${json.msg}`;
            zona.querySelector('p').style.color = '#E53E3E';
        }
    } catch (err) {
        mostrarToast('Error subiendo imagen: ' + err.message, 'error');
    }
}

// ================================================================
// TEST SMTP REAL — fetch a Flask
// ================================================================

async function testSmtp() {
    const btn    = document.getElementById('btnTestSmtp');
    const result = document.getElementById('smtpTestResult');

    const payload = {
        smtp_host:     getVal('cfg_smtp_host'),
        smtp_port:     getNum('cfg_smtp_port'),
        smtp_user:     getVal('cfg_smtp_user'),
        smtp_pass:     getVal('cfg_smtp_pass'),
        smtp_name:     getVal('cfg_smtp_name'),
        email_destino: getVal('cfg_test_email')
    };

    if (!payload.smtp_host || !payload.smtp_user || !payload.smtp_pass) {
        mostrarToast('Completa el servidor, usuario y contraseña SMTP primero', 'error');
        return;
    }
    if (!payload.email_destino) {
        mostrarToast('Ingresa un email de destino para la prueba', 'error');
        return;
    }

    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
    btn.disabled  = true;
    result.className = 'test-result hidden';

    try {
        const res  = await fetch('/admin/api/config/test-smtp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const json = await res.json();

        result.classList.remove('hidden');
        if (json.ok) {
            result.className = 'test-result success';
            result.innerHTML = `<i class="fas fa-check-circle"></i> ${json.msg}`;
        } else {
            result.className = 'test-result error';
            result.innerHTML = `<i class="fas fa-times-circle"></i> ${json.msg}`;
        }
    } catch (err) {
        result.className = 'test-result error';
        result.innerHTML = `<i class="fas fa-times-circle"></i> Error de conexión: ${err.message}`;
        result.classList.remove('hidden');
    } finally {
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar prueba';
        btn.disabled  = false;
    }
}

// ================================================================
// INFO DEL SISTEMA — fetch a Flask
// ================================================================

async function cargarInfoSistema() {
    try {
        const res  = await fetch('/admin/api/config/sistema-info');
        const json = await res.json();
        if (json.ok) {
            const d = json.datos;
            setEl('sys-python',  d.python  || '—');
            setEl('sys-flask',   d.flask   || '—');
            setEl('sys-storage', d.storage || 'JSON Local');
        }
    } catch {
        setEl('sys-python', 'N/A');
        setEl('sys-flask',  'N/A');
    }
}

function setEl(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// ================================================================
// LIMPIAR CACHÉ — fetch a Flask
// ================================================================

async function limpiarCache() {
    const btn = document.getElementById('btnLimpiarCache');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Limpiando...';
    btn.disabled  = true;

    try {
        const res  = await fetch('/admin/api/config/limpiar-cache', { method: 'POST' });
        const json = await res.json();
        mostrarToast(json.msg, json.ok ? 'success' : 'error');
    } catch (err) {
        mostrarToast('Error: ' + err.message, 'error');
    } finally {
        btn.innerHTML = '<i class="fas fa-trash-alt"></i> Limpiar Caché Ahora';
        btn.disabled  = false;
    }
}

// ================================================================
// EXPORTAR ZIP — descarga directa desde Flask
// ================================================================

function exportarDatos() {
    const btn = document.getElementById('btnExportar');
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generando...';
    btn.disabled  = true;

    // Crear enlace de descarga apuntando al endpoint Flask
    const a = document.createElement('a');
    a.href  = '/admin/api/config/exportar';
    a.click();

    setTimeout(() => {
        btn.innerHTML = '<i class="fas fa-download"></i> Exportar ZIP';
        btn.disabled  = false;
        mostrarToast('Descarga iniciada', 'success');
    }, 2000);
}

// ================================================================
// RESET DE DATOS
// ================================================================

function confirmarReset() {
    mostrarConfirm(
        '⚠️ ACCIÓN IRREVERSIBLE',
        'Esto borrará TODOS los datos del sistema. ¿Estás completamente seguro?',
        async () => {
            mostrarToast('Función de reset no implementada en producción', 'error');
            // Descomenta cuando tengas el endpoint:
            // await fetch('/admin/api/config/reset-datos', { method: 'POST' });
            // location.reload();
        }
    );
}

// ================================================================
// SELECTOR DE MOTOR DE BD + GENERADORES DE URL
// ================================================================

function selectEngine(engine) {
    document.querySelectorAll('.db-engine-card').forEach(c => c.classList.remove('active'));
    document.querySelector(`[data-engine="${engine}"]`)?.classList.add('active');
    document.querySelectorAll('.db-config-panel').forEach(p => p.classList.add('hidden'));
    document.getElementById(`db-${engine}-config`)?.classList.remove('hidden');
}

function initDBListeners() {
    // SQLite
    document.getElementById('cfg_sqlite_path')?.addEventListener('input', function () {
        const url = document.getElementById('sqlite-url');
        if (url) url.textContent = `sqlite:///${this.value}`;
    });

    // PostgreSQL
    ['cfg_pg_host','cfg_pg_port','cfg_pg_db','cfg_pg_user','cfg_pg_pass'].forEach(id => {
        document.getElementById(id)?.addEventListener('input', function () {
            const h = getVal('cfg_pg_host') || 'localhost';
            const p = getVal('cfg_pg_port') || '5432';
            const d = getVal('cfg_pg_db')   || 'villacutupu_db';
            const u = getVal('cfg_pg_user') || 'usuario';
            const w = getVal('cfg_pg_pass') || 'contraseña';
            const el = document.getElementById('pg-url');
            if (el) el.textContent = `postgresql://${u}:${w}@${h}:${p}/${d}`;
        });
    });

    // MySQL
    ['cfg_my_host','cfg_my_port','cfg_my_db','cfg_my_user','cfg_my_pass'].forEach(id => {
        document.getElementById(id)?.addEventListener('input', function () {
            const h = getVal('cfg_my_host') || 'localhost';
            const p = getVal('cfg_my_port') || '3306';
            const d = getVal('cfg_my_db')   || 'villacutupu_db';
            const u = getVal('cfg_my_user') || 'usuario';
            const w = getVal('cfg_my_pass') || 'contraseña';
            const el = document.getElementById('my-url');
            if (el) el.textContent = `mysql+pymysql://${u}:${w}@${h}:${p}/${d}`;
        });
    });
}

// ================================================================
// TEMAS
// ================================================================

function selectTheme(theme, save = true) {
    document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
    document.querySelector(`[data-theme="${theme}"]`)?.classList.add('active');
}

// ================================================================
// COLORES SINCRONIZADOS
// ================================================================

function initColorInputs() {
    [
        ['cfg_color_primary', 'cfg_color_primary_hex'],
        ['cfg_color_accent',  'cfg_color_accent_hex'],
        ['cfg_color_sidebar', 'cfg_color_sidebar_hex'],
    ].forEach(([colorId, hexId]) => {
        const colorEl = document.getElementById(colorId);
        const hexEl   = document.getElementById(hexId);
        if (!colorEl || !hexEl) return;

        colorEl.addEventListener('input', () => hexEl.value = colorEl.value);
        hexEl.addEventListener('input', () => {
            if (/^#[0-9A-Fa-f]{6}$/.test(hexEl.value)) colorEl.value = hexEl.value;
        });
    });
}

// ================================================================
// TOGGLE PASSWORD
// ================================================================

function togglePassword(inputId) {
    const el  = document.getElementById(inputId);
    const ico = el?.parentElement.querySelector('.toggle-pass i');
    if (!el || !ico) return;
    el.type     = el.type === 'password' ? 'text' : 'password';
    ico.className = el.type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
}

// ================================================================
// COPIAR AL PORTAPAPELES
// ================================================================

function copyText(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    navigator.clipboard.writeText(el.textContent).then(() => {
        mostrarToast('Copiado al portapapeles', 'success');
    });
}

// ================================================================
// TOAST
// ================================================================

let toastTimer;

function mostrarToast(msg, tipo = 'success') {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toastMsg');
    const ico   = document.getElementById('toastIcon');
    if (!toast || !msgEl) return;

    msgEl.textContent = msg;
    if (ico) ico.className = tipo === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    toast.style.background = tipo === 'success' ? '#2d4a2d' : '#C53030';

    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 3500);
}

// ================================================================
// MODAL DE CONFIRMACIÓN
// ================================================================

let confirmCb = null;

function mostrarConfirm(titulo, msg, cb) {
    const modal = document.getElementById('confirmModal');
    if (!modal) { if (confirm(msg)) cb(); return; }

    document.getElementById('confirmTitle').textContent = titulo;
    document.getElementById('confirmMsg').textContent   = msg;
    confirmCb = cb;

    document.getElementById('confirmBtn').onclick = () => {
        closeModal();
        if (typeof confirmCb === 'function') confirmCb();
    };

    modal.classList.add('show');
}

function closeModal() {
    document.getElementById('confirmModal')?.classList.remove('show');
    confirmCb = null;
}

document.addEventListener('click', e => {
    if (e.target.id === 'confirmModal') closeModal();
});
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
});