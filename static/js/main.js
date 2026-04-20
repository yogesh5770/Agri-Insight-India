document.addEventListener('DOMContentLoaded', () => {
    // State Management
    let currentTab = 'trends';
    let chartInstance = null;

    // Elements
    const stateSelect = document.getElementById('stateSelect');
    const districtSelect = document.getElementById('districtSelect');
    const cropSelect = document.getElementById('cropSelect');
    const metricSelect = document.getElementById('metricSelect');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const chartCtx = document.getElementById('analyticsChart').getContext('2d');
    const resultOverlay = document.getElementById('predictionResult');

    // Initialize States
    fetch('/api/states')
        .then(res => res.json())
        .then(states => {
            states.forEach(state => {
                const opt = document.createElement('option');
                opt.value = state;
                opt.textContent = state;
                stateSelect.appendChild(opt);
            });
        });

    // State -> District Linkage
    stateSelect.addEventListener('change', () => {
        const state = stateSelect.value;
        districtSelect.innerHTML = '<option value="">Select District</option>';
        if (!state) return;

        fetch(`/api/districts?state=${encodeURIComponent(state)}`)
            .then(res => res.json())
            .then(districts => {
                districts.forEach(dist => {
                    const opt = document.createElement('option');
                    opt.value = dist;
                    opt.textContent = dist;
                    districtSelect.appendChild(opt);
                });
            });
    });

    // Fetch and Render Trends
    const updateChart = () => {
        const state = stateSelect.value;
        const district = districtSelect.value;
        const crop = cropSelect.value;
        const metric = metricSelect.value;

        if (!district || !state) return;

        fetch(`/api/crop_trends?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}&crop=${encodeURIComponent(crop)}&metric=${encodeURIComponent(metric)}&t=${Date.now()}`)
            .then(res => res.json())
            .then(data => {
                const labels = data.map(d => d.Year);
                const values = data.map(d => d.Value);

                if (chartInstance) chartInstance.destroy();

                chartInstance = new Chart(chartCtx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: `${crop} ${metric}`,
                            data: data.map(d => ({
                                x: d.Year,
                                y: d.Value,
                                is_predicted: d.is_predicted
                            })),
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: data.map(d => d.is_predicted ? 2 : 4),
                            segment: {
                                borderDash: ctx => ctx.p1.raw.is_predicted ? [5, 5] : undefined,
                                borderColor: ctx => ctx.p1.raw.is_predicted ? '#6ee7b7' : '#10b981'
                            }
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#f8fafc' }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) label += ': ';
                                        if (context.parsed.y !== null) {
                                            label += context.parsed.y.toFixed(2);
                                        }
                                        if (context.raw.is_predicted) {
                                            label += ' (Predicted)';
                                        }
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#94a3b8' } },
                            x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                        }
                    }
                });
            });
            
        // Also fetch top crops for the sidebar/cards
        fetch(`/api/top_crops?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`)
            .then(res => res.json())
            .then(crops => {
                const container = document.getElementById('topCropsList');
                container.innerHTML = '';
                crops.forEach(c => {
                    const div = document.createElement('div');
                    div.className = 'glass-card animate-in';
                    div.style.marginBottom = '0.5rem';
                    div.innerHTML = `<strong>${c.crop}</strong>: ${c.yield.toFixed(2)} Kg/ha`;
                    container.appendChild(div);
                });
            });
    };

    analyzeBtn.addEventListener('click', updateChart);

    // Tab Switching
    window.switchTab = (tab) => {
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        event.target.classList.add('active');
        
        document.getElementById('trendsView').style.display = tab === 'trends' ? 'block' : 'none';
        document.getElementById('predictView').style.display = tab === 'predict' ? 'block' : 'none';
    };

    // ML Prediction Handler
    const predictForm = document.getElementById('predictForm');
    predictForm?.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(predictForm);
        const data = Object.fromEntries(formData.entries());

        fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(res => {
            resultOverlay.style.display = 'block';
            resultOverlay.innerHTML = `<h3>Prediction Result</h3><p>${res.result}</p>`;
        });
    });
});
