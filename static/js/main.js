
const socket = io();

// Tab Management
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('d-none');
    });
    document.getElementById(`${tabName}-tab`).classList.remove('d-none');

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active text-primary');
    });

    if (tabName === 'announcements') loadAnnouncements();
    if (tabName === 'eod') loadEODHistory();
    if (tabName === 'backtest') loadBacktest();
}

function loadBacktest() {
    const tbody = document.getElementById('backtest-body');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-5">Connecting to Backtest Engine...</td></tr>';

    fetch('/get_backtest_stats')
        .then(res => res.json())
        .then(data => {
            if (data && data.length > 0) {
                tbody.innerHTML = data.map(r => `
                    <tr>
                        <td class="ps-4">
                            <div class="fw-bold text-light">${r.strategy}</div>
                            <div class="text-secondary x-small">100+ Signals</div>
                        </td>
                        <td>${r.period}</td>
                        <td class="text-info fw-bold">${r.total_signals}</td>
                        <td class="text-success">+${r.avg_return}%</td>
                        <td class="text-end pe-4">
                            <span class="badge bg-primary fs-6">${r.accuracy}% Accuracy</span>
                        </td>
                    </tr>
                `).join('');
            } else {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center py-5">
                            <p class="text-secondary">No backtest data found.</p>
                            <button class="btn btn-primary" onclick="triggerBacktest()">Start 1-Year Analysis</button>
                        </td>
                    </tr>
                `;
            }
        });
}

function triggerBacktest() {
    const tbody = document.getElementById('backtest-body');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-5"><div class="spinner-border text-primary"></div><br>Analysis Started! It will take 2-3 minutes to process 1 year of data. You can check back later.</td></tr>';

    fetch('/api/run-backtest')
        .then(res => res.json())
        .then(() => {
            setTimeout(loadBacktest, 5000); // Check status after 5s
        });
}

// Socket.IO Connection
let lastRecommendation = null;

socket.on('connect', () => {
    console.log('Connected to Trade with Nilay Terminal');
    document.getElementById('market-status').innerHTML = '<i class="bi bi-circle-fill small me-1"></i> LIVE';
    document.getElementById('market-status').classList.add('text-info');
});

socket.on('market_update', (data) => {
    console.log('Market Update Received:', data);
    const stocks = data.stocks || [];
    if (stocks.length > 0) {
        updateDashboardTable(stocks);

        // Instant Pick Logic: Strongest stock first
        const strongest = stocks.reduce((prev, current) => (prev.change_pct > current.change_pct) ? prev : current);
        if (strongest && strongest.symbol !== lastRecommendation && strongest.change_pct > 2.0) {
            lastRecommendation = strongest.symbol;
            showInstantPopup(strongest);
        }
    }
    document.getElementById('last-update-time').innerText = new Date().toLocaleTimeString();
});

function updateDashboardTable(stocks) {
    const tbody = document.getElementById('dashboard-body');
    if (!stocks || stocks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-5 text-secondary">No stocks currently in the 0-3% range.</td></tr>';
        return;
    }

    tbody.innerHTML = stocks.map(stock => `
        <tr>
            <td class="ps-4">
                <div class="fw-bold text-light">${stock.symbol}</div>
                <div class="text-secondary x-small">NSE Equity</div>
            </td>
            <td>₹${Number(stock.price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
            <td>
                <span class="badge ${stock.change_pct > 0 ? 'bg-success' : 'bg-danger'}">
                    ${stock.change_pct > 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%
                </span>
            </td>
            <td class="text-secondary small">${Number(stock.volume).toLocaleString('en-IN')}</td>
            <td class="text-secondary small">Just Now</td>
            <td class="text-end pe-4">
                <button class="btn btn-outline-primary btn-sm" onclick="showAIReport('${stock.symbol}')">
                    <i class="bi bi-cpu"></i> AI Report
                </button>
            </td>
        </tr>
    `).join('');

    document.getElementById('total-results').innerText = stocks.length;
}

// AI Report Modal
function showAIReport(symbol) {
    const modal = new bootstrap.Modal(document.getElementById('aiModal'));
    const content = document.getElementById('ai-report-content');
    modal.show();

    fetch(`/api/ai-report/${symbol}`)
        .then(res => res.json())
        .then(data => {
            content.innerHTML = `
                <div class="row g-3">
                    <div class="col-6">
                        <div class="p-3 bg-black rounded border border-secondary text-center">
                            <div class="text-secondary x-small uppercase">PE RATIO</div>
                            <div class="h4 mb-0 fw-bold">${data.pe_ratio || 'N/A'}</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="p-3 bg-black rounded border border-secondary text-center">
                            <div class="text-secondary x-small uppercase">ROE %</div>
                            <div class="h4 mb-0 fw-bold">${data.roe ? data.roe.toFixed(2) + '%' : 'N/A'}</div>
                        </div>
                    </div>
                    <div class="col-12">
                        <h6 class="text-primary fw-bold mt-2"><i class="bi bi-journal-text me-2"></i>Fundamentals</h6>
                        <p class="text-secondary small">${data.fundamental_summary}</p>
                    </div>
                    <div class="col-12">
                        <div class="p-3 bg-primary bg-opacity-10 rounded border border-primary border-opacity-25">
                            <h6 class="text-primary fw-bold mb-2"><i class="bi bi-lightning-charge-fill me-2"></i>AI INSIGHT</h6>
                            <p class="mb-0 fw-medium">${data.ai_insights}</p>
                        </div>
                    </div>
                </div>
            `;
        });
}

// Scanners Loader
function loadScanner(type) {
    const container = document.getElementById(`${type}-scanner-body`);
    fetch(`/scan-now?type=${type}`)
        .then(res => res.json())
        .then(data => {
            const stocks = data.results || [];
            if (stocks.length === 0) {
                const cols = (type === 'vcp' || type === 'smc') ? 6 : (type === 'chartink' ? 5 : 5);
                container.innerHTML = `<tr><td colspan="${cols}" class="text-center py-4 text-secondary">No stocks found.</td></tr>`;
                return;
            }

            if (type === 'vcp') {
                container.innerHTML = stocks.map(stock => `
                    <tr>
                        <td class="ps-4">
                            <div class="fw-bold text-light">${stock.symbol}</div>
                            <div class="text-secondary x-small">VCP Candidate</div>
                        </td>
                        <td>₹${stock.price.toFixed(2)}</td>
                        <td><span class="badge ${stock.change_pct >= 0 ? 'bg-success' : 'bg-danger'}">${stock.change_pct.toFixed(2)}%</span></td>
                        <td class="fw-bold text-warning">${stock.patterns}</td>
                        <td class="text-secondary small">${stock.indicators}</td>
                        <td class="text-end pe-4">
                            <button class="btn btn-sm btn-outline-danger" onclick="showAIReport('${stock.symbol}')">VCP Research</button>
                        </td>
                    </tr>
                `).join('');
            } else if (type === 'chartink') {
                container.innerHTML = stocks.map(stock => `
                    <tr>
                        <td class="ps-4 fw-bold">${stock.symbol}</td>
                        <td>₹${stock.price.toFixed(2)}</td>
                        <td><span class="badge ${stock.change_pct >= 0 ? 'bg-success' : 'bg-danger'}">${stock.change_pct.toFixed(2)}%</span></td>
                        <td class="text-info small">${stock.patterns}</td>
                        <td class="text-end pe-4">
                            <button class="btn btn-sm btn-outline-info" onclick="showAIReport('${stock.symbol}')">Research</button>
                        </td>
                    </tr>
                `).join('');
            } else if (type === 'smc') {
                container.innerHTML = stocks.map(stock => `
                    <tr>
                        <td class="ps-4 fw-bold">${stock.symbol}</td>
                        <td>₹${stock.price.toFixed(2)}</td>
                        <td><span class="badge ${stock.change_pct >= 0 ? 'bg-success' : 'bg-danger'}">${stock.change_pct.toFixed(2)}%</span></td>
                        <td class="text-warning fw-bold">${stock.patterns}</td>
                        <td class="text-secondary small">${stock.indicators}</td>
                        <td class="text-end pe-4">
                            <button class="btn btn-sm btn-outline-primary" onclick="showAIReport('${stock.symbol}')">Institutional Research</button>
                        </td>
                    </tr>
                `).join('');
            } else {
                container.innerHTML = stocks.map(stock => `
                    <tr>
                        <td class="ps-4 fw-bold">${stock.symbol}</td>
                        <td>₹${stock.price.toFixed(2)}</td>
                        <td><span class="text-${stock.change_pct >= 0 ? 'success' : 'danger'}">${stock.change_pct.toFixed(2)}%</span></td>
                        <td class="small text-secondary">${stock.volume.toLocaleString()}</td>
                        <td class="text-end pe-4">
                            <button class="btn btn-sm btn-outline-info" onclick="showAIReport('${stock.symbol}')">Research</button>
                        </td>
                    </tr>
                `).join('');
            }
        });
}

// Announcements Loader
function loadAnnouncements(query = '') {
    const container = document.getElementById('announcements-list');
    fetch(`/api/announcements?q=${query}`)
        .then(res => res.json())
        .then(data => {
            if (data.length === 0) {
                container.innerHTML = '<div class="col-12 text-center py-5 text-secondary">No announcements found.</div>';
                return;
            }
            container.innerHTML = data.map(ann => `
                <div class="col-md-6 mb-3">
                    <div class="card bg-dark border-${ann.is_important ? 'danger' : 'secondary'} h-100 shadow-sm animate-fade-in">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <span class="badge bg-primary">${ann.symbol}</span>
                                ${ann.is_important ? '<span class="badge bg-danger pulse-red"><i class="bi bi-exclamation-triangle-fill"></i> HIGH IMPACT</span>' : ''}
                                <small class="text-secondary">${new Date(ann.ann_date).toLocaleDateString()}</small>
                            </div>
                            <h6 class="card-title text-light fw-bold mb-2">${ann.title}</h6>
                            <p class="card-text text-secondary small mb-3 text-truncate-2">${ann.description}</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="badge bg-dark border border-secondary text-secondary">${ann.category}</span>
                                <a href="${ann.link}" target="_blank" class="btn btn-sm btn-outline-info ${ann.link ? '' : 'disabled'}">
                                    <i class="bi bi-file-earmark-pdf"></i> View PDF
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        });
}

// EOD History Loader
function loadEODHistory() {
    const container = document.getElementById('eod-container');
    fetch('/api/eod-history')
        .then(res => res.json())
        .then(data => {
            if (data.length === 0) {
                container.innerHTML = '<div class="text-center py-5 text-secondary">No EOD history available yet.</div>';
                return;
            }
            container.innerHTML = data.map(report => {
                const breadth = JSON.parse(report.market_breadth);
                return `
                <div class="card bg-black mb-3 border-secondary overflow-hidden">
                    <div class="card-header bg-dark border-secondary d-flex justify-content-between">
                        <span class="fw-bold text-primary">${report.report_date}</span>
                        <span class="text-secondary small">Advances: ${breadth.advances} | Declines: ${breadth.declines}</span>
                    </div>
                    <div class="card-body">
                        <p class="card-text small text-secondary">${report.summary}</p>
                        <div class="row g-2">
                            <div class="col-md-6">
                                <small class="text-success fw-bold uppercase x-small">Top Gainers</small>
                                <div class="text-light small mt-1">
                                    ${JSON.parse(report.top_gainers).map(g => g.symbol).join(', ')}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <small class="text-danger fw-bold uppercase x-small">Top Losers</small>
                                <div class="text-light small mt-1">
                                    ${JSON.parse(report.top_losers).map(l => l.symbol).join(', ')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                `;
            }).join('');
        });
}

function filterAnnouncements() {
    const query = document.getElementById('ann-search').value;
    loadAnnouncements(query);
}

// Initial Load
window.addEventListener('load', () => {
    // Check if on dashboard, set update timer
    setInterval(() => {
        const isDashboardVisible = !document.getElementById('dashboard-tab').classList.contains('d-none');
        if (isDashboardVisible) {
            fetch('/api/dashboard')
                .then(res => res.json())
                .then(data => {
                    const stocks = data;
                    if (stocks.length > 0) {
                        updateDashboardTable(stocks);

                        // Check for instant popup (Strongest stock first)
                        const strongest = stocks.reduce((prev, current) => (prev.change_pct > current.change_pct) ? prev : current);
                        if (strongest && strongest.symbol !== lastRecommendation && strongest.change_pct > 2.0) {
                            lastRecommendation = strongest.symbol;
                            showInstantPopup(strongest);
                        }
                    }
                });
        }
    }, 30000); // Faster update (30s)

    function showInstantPopup(stock) {
        document.getElementById('rec-symbol').innerText = stock.symbol;
        document.getElementById('rec-reason').innerText = `Strong Signal: ${stock.patterns || 'Swing Pick'} | ${stock.change_pct}%`;
        const modal = new bootstrap.Modal(document.getElementById('recommendModal'));
        modal.show();
    }

    function launchRecReport() {
        const symbol = document.getElementById('rec-symbol').innerText;
        showAIReport(symbol);
    }

    // Check Scan Status
    setInterval(() => {
        fetch('/api/scan-status')
            .then(res => res.json())
            .then(data => {
                const statusEl = document.getElementById('market-status');
                if (data.is_scanning) {
                    statusEl.innerHTML = '<i class="bi bi-circle-fill small me-1"></i> SCANNING...';
                    statusEl.classList.remove('text-info');
                    statusEl.classList.add('text-warning');
                } else {
                    statusEl.innerHTML = '<i class="bi bi-circle-fill small me-1"></i> LIVE';
                    statusEl.classList.remove('text-warning');
                    statusEl.classList.add('text-info');
                }
            });
    }, 5000);
});
