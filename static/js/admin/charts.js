// static/js/admin-charts.js

let solicitudesChart, denunciasPieChart;

function initCharts(solicitudesData, denunciasData) {
    // Verificar que Chart.js está disponible
    if (typeof Chart === 'undefined') {
        console.error('Chart.js no está cargado');
        return;
    }

    // Gráfico de solicitudes
    const ctxSolicitudes = document.getElementById('solicitudesChart')?.getContext('2d');
    if (ctxSolicitudes) {
        if (solicitudesChart) solicitudesChart.destroy();
        solicitudesChart = new Chart(ctxSolicitudes, {
            type: 'line',
            data: solicitudesData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        console.log('Gráfico de solicitudes inicializado');
    }

    // Gráfico de denuncias (pastel)
    const ctxDenuncias = document.getElementById('denunciasPieChart')?.getContext('2d');
    if (ctxDenuncias) {
        if (denunciasPieChart) denunciasPieChart.destroy();
        denunciasPieChart = new Chart(ctxDenuncias, {
            type: 'pie',
            data: denunciasData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        console.log('Gráfico de denuncias inicializado');
    }
}

function changeChartPeriod(period) {
    // Actualizar botones
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Aquí puedes cargar datos diferentes según el período
    console.log('Cambiando período a:', period);
}

function quickAction(type, id) {
    // Implementar acción rápida
    console.log('Acción rápida:', type, id);
}

function exportReport() {
    // Implementar exportación
    alert('Función de exportación próximamente disponible');
}

function closeModal() {
    document.getElementById('quickActionModal').classList.remove('show');
    document.querySelector('.modal-backdrop')?.remove();
}

let refreshInterval;

function startAutoRefresh(interval) {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(() => {
        // Recargar datos sin recargar la página
        fetch('/admin/api/estadisticas')
            .then(response => response.json())
            .then(data => {
                console.log('Datos actualizados:', data);
                // Actualizar estadísticas en la UI
                updateStats(data);
            })
            .catch(err => console.error('Error actualizando datos:', err));
    }, interval);
}

function updateStats(data) {
    // Actualizar números en las tarjetas
    if (data.usuarios) {
        document.querySelectorAll('.stat-number')[0].textContent = data.usuarios.total || 0;
    }
    if (data.solicitudes) {
        document.querySelectorAll('.stat-number')[1].textContent = data.solicitudes.total || 0;
    }
    if (data.denuncias) {
        document.querySelectorAll('.stat-number')[2].textContent = data.denuncias.total || 0;
    }
}