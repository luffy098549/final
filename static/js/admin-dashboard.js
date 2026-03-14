// static/js/admin-dashboard.js
// DASHBOARD ESPECÍFICO

let solicitudesChart, denunciasPieChart;

function initCharts(solicitudesData, denunciasData) {
    initSolicitudesChart(solicitudesData);
    initDenunciasPieChart(denunciasData);
}

function initSolicitudesChart(data) {
    const ctx = document.getElementById('solicitudesChart')?.getContext('2d');
    if (!ctx) return;
    
    if (solicitudesChart) {
        solicitudesChart.destroy();
    }
    
    solicitudesChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#fff',
                    bodyColor: '#94a3b8',
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#e2e8f0',
                        drawBorder: false
                    },
                    ticks: {
                        stepSize: 5,
                        color: '#64748b'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#64748b'
                    }
                }
            }
        }
    });
}

function initDenunciasPieChart(data) {
    const ctx = document.getElementById('denunciasPieChart')?.getContext('2d');
    if (!ctx) return;
    
    if (denunciasPieChart) {
        denunciasPieChart.destroy();
    }
    
    denunciasPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#64748b',
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#fff',
                    bodyColor: '#94a3b8'
                }
            }
        }
    });
}

function changeChartPeriod(period) {
    // Actualizar botones
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Cargar nuevos datos
    fetch(`/admin/api/solicitudes?periodo=${period}`)
        .then(response => response.json())
        .then(data => {
            solicitudesChart.data.labels = data.labels;
            solicitudesChart.data.datasets[0].data = data.values;
            solicitudesChart.update();
        });
}