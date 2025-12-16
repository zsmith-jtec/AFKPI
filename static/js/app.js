/**
 * AFKPI Application Logic
 * Dashboard initialization and data loading
 */

// Current state
let currentWeekId = null;
let weeksData = [];

/**
 * Initialize dashboard
 */
async function initDashboard() {
    try {
        // Set user name in navbar
        const user = api.getUser();
        if (user) {
            document.getElementById('user-name').textContent = user.name || user.email;
        }

        // Load weeks for dropdown
        await loadWeeks();

        // Load dashboard data for current week
        await loadDashboardData();

    } catch (error) {
        console.error('Dashboard init error:', error);
        showError('Failed to load dashboard data');
    }
}

/**
 * Load available weeks into dropdown
 */
async function loadWeeks() {
    const weeks = await api.get('/api/weeks');
    weeksData = weeks;

    const selector = document.getElementById('week-selector');
    selector.innerHTML = '';

    weeks.forEach((week, index) => {
        const option = document.createElement('option');
        option.value = week.week_id;
        option.textContent = week.label;
        if (index === 0) {
            option.selected = true;
            currentWeekId = week.week_id;
        }
        selector.appendChild(option);
    });

    // Add change listener
    selector.addEventListener('change', function() {
        currentWeekId = parseInt(this.value);
        loadDashboardData();
    });
}

/**
 * Load all dashboard data
 */
async function loadDashboardData() {
    showLoading(true);

    try {
        // Update week label
        const week = weeksData.find(w => w.week_id === currentWeekId);
        if (week) {
            document.getElementById('week-label').textContent = `Week ${week.label}`;
        }

        // Load data in parallel
        const [revenueData, marginData, laborData, marginTrend] = await Promise.all([
            api.get(`/api/revenue?week_id=${currentWeekId}`),
            api.get(`/api/margin?week_id=${currentWeekId}`),
            api.get(`/api/labor?week_id=${currentWeekId}`),
            api.get('/api/margin/trend?weeks=13')
        ]);

        // Update KPI cards
        updateKPICards(revenueData, marginData, laborData);

        // Update charts
        renderRevenueChart(revenueData.by_product);
        renderMarginTrendChart(marginTrend);

        // Update jobs table
        updateJobsTable(laborData.by_job);

        showLoading(false);

    } catch (error) {
        console.error('Data load error:', error);
        showError('Failed to load data');
        showLoading(false);
    }
}

/**
 * Update KPI cards with data
 */
function updateKPICards(revenue, margin, labor) {
    // Revenue card
    document.getElementById('kpi-revenue').textContent = api.formatCurrency(revenue.total_outbound);

    // Margin card
    const marginEl = document.getElementById('kpi-margin');
    marginEl.textContent = api.formatPercent(margin.overall_margin_percent);

    // Color code margin vs target (30%)
    const targetMargin = 30;
    if (parseFloat(margin.overall_margin_percent) >= targetMargin) {
        marginEl.classList.add('text-success');
        marginEl.classList.remove('text-danger');
    } else {
        marginEl.classList.add('text-danger');
        marginEl.classList.remove('text-success');
    }
    document.getElementById('kpi-margin-target').textContent = `Target: ${targetMargin}%`;

    // Labor card
    document.getElementById('kpi-labor').textContent = api.formatCurrency(labor.total_labor_cost);
    document.getElementById('kpi-labor-jobs').textContent = `${labor.job_count} jobs`;
}

/**
 * Update jobs table
 */
function updateJobsTable(jobs) {
    const tbody = document.getElementById('jobs-table-body');
    tbody.innerHTML = '';

    // Show top 10 jobs
    const topJobs = jobs.slice(0, 10);

    topJobs.forEach(job => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><a href="#" onclick="showJobDetail('${job.job_num}')">${job.job_num}</a></td>
            <td>${job.sales_order_num || '--'}</td>
            <td>${job.product_group || '--'}</td>
            <td class="text-end">${api.formatCurrency(job.direct_labor)}</td>
            <td class="text-end">${api.formatCurrency(job.burden)}</td>
            <td class="text-end"><strong>${api.formatCurrency(job.total_cost)}</strong></td>
        `;
        tbody.appendChild(row);
    });

    if (topJobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No job data available</td></tr>';
    }
}

/**
 * Show job detail (placeholder for drill-down)
 */
function showJobDetail(jobNum) {
    alert(`Job detail for ${jobNum} - Coming soon!`);
}

/**
 * Show/hide loading spinner
 */
function showLoading(show) {
    const spinner = document.getElementById('loading-spinner');
    const content = document.getElementById('dashboard-content');

    if (show) {
        spinner.classList.remove('d-none');
        content.classList.add('d-none');
    } else {
        spinner.classList.add('d-none');
        content.classList.remove('d-none');
    }
}

/**
 * Show error message
 */
function showError(message) {
    alert(message); // Simple for now, can enhance with toast
}
