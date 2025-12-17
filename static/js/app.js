/**
 * FOS Application Logic
 * Dashboard initialization and data loading
 */

// Current state
let currentWeekId = null;
let weeksData = [];
let currentJobFilter = 'all';  // 'all', 'wip', or 'completed'
let periodType = 'weekly';  // 'weekly' or 'monthly'
let monthsData = [];
let currentMonthWeekIds = [];  // Week IDs for currently selected month

/**
 * Initialize dashboard
 */
async function initDashboard() {
  try {
    // Set user name in navbar
    const user = api.getUser();
    if (user) {
      document.getElementById("user-name").textContent =
        user.name || user.email;
    }

    // Load weeks for dropdown
    await loadWeeks();

    // Load dashboard data for current week
    await loadDashboardData();
  } catch (error) {
    console.error("Dashboard init error:", error);
    showError("Failed to load dashboard data");
  }
}

/**
 * Set period type (weekly or monthly)
 */
async function setPeriodType(type) {
  periodType = type;

  // Update button states
  const weeklyBtn = document.getElementById('period-weekly');
  const monthlyBtn = document.getElementById('period-monthly');
  if (weeklyBtn && monthlyBtn) {
    weeklyBtn.classList.toggle('active', type === 'weekly');
    monthlyBtn.classList.toggle('active', type === 'monthly');
  }

  // Load appropriate data into selector
  if (type === 'weekly') {
    await populateWeekSelector();
  } else {
    await populateMonthSelector();
  }

  // Reload current page data
  const path = window.location.pathname;
  if (path === "/revenue") {
    loadRevenueData();
  } else if (path === "/margin") {
    loadMarginData();
  } else if (path === "/labor") {
    loadLaborData();
  } else {
    loadDashboardData();
  }
}

/**
 * Load available weeks into dropdown
 */
async function loadWeeks() {
  // Load both weeks and months data
  const [weeks, months] = await Promise.all([
    api.get("/api/weeks"),
    api.get("/api/weeks/months")
  ]);
  weeksData = weeks;
  monthsData = months;

  // Populate based on current period type
  if (periodType === 'weekly') {
    populateWeekSelector();
  } else {
    populateMonthSelector();
  }

  // Add change listener to dropdown
  const selector = document.getElementById("week-selector");
  selector.addEventListener("change", handlePeriodChange);

  // Initialize timeline slider
  initTimelineSlider();
}

/**
 * Initialize the timeline slider
 */
function initTimelineSlider() {
  const slider = document.getElementById("timeline-slider");
  if (!slider || weeksData.length === 0) return;

  // Set slider range (reversed: 0 = most recent, max = oldest)
  slider.min = 0;
  slider.max = weeksData.length - 1;
  slider.value = 0;

  // Update labels
  updateSliderLabels();

  // Add event listener
  slider.addEventListener("input", handleSliderChange);
}

/**
 * Update slider labels based on current data
 */
function updateSliderLabels() {
  const startLabel = document.getElementById("timeline-start");
  const endLabel = document.getElementById("timeline-end");
  const currentLabel = document.getElementById("timeline-current");

  if (!startLabel || !endLabel || !currentLabel) return;

  if (weeksData.length > 0) {
    // Most recent week (slider position 0)
    startLabel.textContent = weeksData[0].label;
    // Oldest week (slider max position)
    endLabel.textContent = weeksData[weeksData.length - 1].label;
    // Current selection
    const currentIdx = parseInt(document.getElementById("timeline-slider")?.value || 0);
    currentLabel.textContent = weeksData[currentIdx]?.label || "--";
  }
}

/**
 * Handle timeline slider change
 */
function handleSliderChange(e) {
  const idx = parseInt(e.target.value);
  if (idx >= 0 && idx < weeksData.length) {
    const week = weeksData[idx];
    currentWeekId = week.week_id;
    currentMonthWeekIds = [week.week_id];

    // Update dropdown to match
    const selector = document.getElementById("week-selector");
    if (selector) selector.value = week.week_id;

    // Update current label
    const currentLabel = document.getElementById("timeline-current");
    if (currentLabel) currentLabel.textContent = week.label;

    // Reload data for current page
    reloadCurrentPage();
  }
}

/**
 * Reload data for the current page
 */
function reloadCurrentPage() {
  const path = window.location.pathname;
  if (path === "/revenue") {
    loadRevenueData();
  } else if (path === "/margin") {
    loadMarginData();
  } else if (path === "/labor") {
    loadLaborData();
  } else {
    loadDashboardData();
  }
}

/**
 * Populate selector with weeks
 */
function populateWeekSelector() {
  const selector = document.getElementById("week-selector");
  selector.innerHTML = "";

  weeksData.forEach((week, index) => {
    const option = document.createElement("option");
    option.value = week.week_id;
    option.textContent = week.label;
    if (index === 0) {
      option.selected = true;
      currentWeekId = week.week_id;
      currentMonthWeekIds = [week.week_id];
    }
    selector.appendChild(option);
  });
}

/**
 * Populate selector with months
 */
function populateMonthSelector() {
  const selector = document.getElementById("week-selector");
  selector.innerHTML = "";

  monthsData.forEach((month, index) => {
    const option = document.createElement("option");
    option.value = month.week_ids.join(',');  // Store all week IDs
    option.textContent = month.label;
    if (index === 0) {
      option.selected = true;
      currentMonthWeekIds = month.week_ids;
      currentWeekId = month.week_ids[0];  // Use first week as primary
    }
    selector.appendChild(option);
  });
}

/**
 * Handle period selector change
 */
function handlePeriodChange() {
  const selector = document.getElementById("week-selector");

  if (periodType === 'weekly') {
    currentWeekId = parseInt(selector.value);
    currentMonthWeekIds = [currentWeekId];

    // Sync slider with dropdown
    const slider = document.getElementById("timeline-slider");
    if (slider) {
      const idx = weeksData.findIndex(w => w.week_id === currentWeekId);
      if (idx >= 0) {
        slider.value = idx;
        const currentLabel = document.getElementById("timeline-current");
        if (currentLabel) currentLabel.textContent = weeksData[idx].label;
      }
    }
  } else {
    // Monthly: value contains comma-separated week IDs
    currentMonthWeekIds = selector.value.split(',').map(id => parseInt(id));
    currentWeekId = currentMonthWeekIds[0];
  }

  // Call appropriate load function based on current page
  reloadCurrentPage();
}

/**
 * Load all dashboard data
 */
async function loadDashboardData() {
  showLoading(true);

  try {
    // Update period label
    const weekLabelEl = document.getElementById("week-label");
    if (periodType === 'monthly' && monthsData.length > 0) {
      const selector = document.getElementById("week-selector");
      const selectedOption = selector.options[selector.selectedIndex];
      weekLabelEl.textContent = selectedOption ? selectedOption.textContent : 'Month --';
    } else {
      const week = weeksData.find((w) => w.week_id === currentWeekId);
      if (week) {
        weekLabelEl.textContent = `Week ${week.label}`;
      }
    }

    // Load data in parallel
    const [revenueData, marginData, laborData, marginTrend] = await Promise.all(
      [
        api.get(`/api/revenue?week_id=${currentWeekId}`),
        api.get(`/api/margin?week_id=${currentWeekId}`),
        api.get(`/api/labor?week_id=${currentWeekId}`),
        api.get("/api/margin/trend?weeks=13"),
      ],
    );

    // Update KPI cards
    updateKPICards(revenueData, marginData, laborData);

    // Update charts
    renderRevenueChart(revenueData.by_product);
    renderMarginTrendChart(marginTrend);

    // Update jobs table
    updateJobsTable(laborData.by_job);

    showLoading(false);
  } catch (error) {
    console.error("Data load error:", error);
    showError("Failed to load data");
    showLoading(false);
  }
}

/**
 * Update KPI cards with data
 */
function updateKPICards(revenue, margin, labor) {
  // Revenue card
  document.getElementById("kpi-revenue").textContent = api.formatCurrency(
    revenue.total_outbound,
  );

  // Margin card
  const marginEl = document.getElementById("kpi-margin");
  marginEl.textContent = api.formatPercent(margin.overall_margin_percent);

  // Color code margin vs target (30%)
  const targetMargin = 30;
  if (parseFloat(margin.overall_margin_percent) >= targetMargin) {
    marginEl.classList.add("text-success");
    marginEl.classList.remove("text-danger");
  } else {
    marginEl.classList.add("text-danger");
    marginEl.classList.remove("text-success");
  }
  document.getElementById("kpi-margin-target").textContent =
    `Target: ${targetMargin}%`;

  // Labor card
  document.getElementById("kpi-labor").textContent = api.formatCurrency(
    labor.total_labor_cost,
  );
  document.getElementById("kpi-labor-jobs").textContent =
    `${labor.job_count} jobs`;
}

/**
 * Update jobs table
 */
function updateJobsTable(jobs) {
  const tbody = document.getElementById("jobs-table-body");
  tbody.innerHTML = "";

  // Show top 10 jobs
  const topJobs = jobs.slice(0, 10);

  topJobs.forEach((job) => {
    const statusBadge = job.job_closed
      ? '<span class="badge bg-secondary">Completed</span>'
      : '<span class="badge bg-success">WIP</span>';
    const row = document.createElement("tr");
    row.innerHTML = `
            <td><a href="#" onclick="showJobDetail('${job.job_num}')">${job.job_num}</a></td>
            <td>${job.sales_order_num || "--"}</td>
            <td>${job.product_group || "--"}</td>
            <td>${statusBadge}</td>
            <td class="text-end">${api.formatCurrency(job.direct_labor)}</td>
            <td class="text-end">${api.formatCurrency(job.burden)}</td>
            <td class="text-end"><strong>${api.formatCurrency(job.total_labor)}</strong></td>
        `;
    tbody.appendChild(row);
  });

  if (topJobs.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="7" class="text-center text-muted">No job data available</td></tr>';
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
  const spinner = document.getElementById("loading-spinner");
  const content =
    document.getElementById("dashboard-content") ||
    document.getElementById("page-content");

  if (show) {
    spinner.classList.remove("d-none");
    if (content) content.classList.add("d-none");
  } else {
    spinner.classList.add("d-none");
    if (content) content.classList.remove("d-none");
  }
}

/**
 * Show error message
 */
function showError(message) {
  alert(message); // Simple for now, can enhance with toast
}

/**
 * Initialize Revenue page
 */
async function initRevenue() {
  try {
    const user = api.getUser();
    if (user) {
      document.getElementById("user-name").textContent =
        user.name || user.email;
    }
    await loadWeeks();
    await loadRevenueData();
  } catch (error) {
    console.error("Revenue init error:", error);
    showError("Failed to load revenue data");
  }
}

/**
 * Load revenue page data
 */
async function loadRevenueData() {
  showLoading(true);
  try {
    const week = weeksData.find((w) => w.week_id === currentWeekId);
    if (week) {
      document.getElementById("week-label").textContent = `Week ${week.label}`;
    }

    const revenueData = await api.get(`/api/revenue?week_id=${currentWeekId}`);

    // Update KPIs
    document.getElementById("kpi-inbound").textContent = api.formatCurrency(
      revenueData.total_inbound || 0,
    );
    document.getElementById("kpi-outbound").textContent = api.formatCurrency(
      revenueData.total_outbound || 0,
    );
    document.getElementById("kpi-orders").textContent =
      revenueData.order_count || 0;

    // Render chart
    renderRevenueChart(revenueData.by_product);

    // Update table
    updateRevenueTable(revenueData.by_product);

    showLoading(false);
  } catch (error) {
    console.error("Revenue load error:", error);
    showError("Failed to load revenue data");
    showLoading(false);
  }
}

/**
 * Update revenue table
 */
function updateRevenueTable(products) {
  const tbody = document.getElementById("revenue-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  (products || []).forEach((p) => {
    const total = (p.inbound || 0) + (p.outbound || 0);
    const row = document.createElement("tr");
    row.innerHTML = `
            <td>${p.product_group}</td>
            <td class="text-end">${api.formatCurrency(p.inbound || 0)}</td>
            <td class="text-end">${api.formatCurrency(p.outbound || 0)}</td>
            <td class="text-end"><strong>${api.formatCurrency(total)}</strong></td>
            <td class="text-end">${p.order_count || 0}</td>
        `;
    tbody.appendChild(row);
  });

  if (!products || products.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="5" class="text-center text-muted">No revenue data available</td></tr>';
  }
}

/**
 * Initialize Margin page
 */
async function initMargin() {
  try {
    const user = api.getUser();
    if (user) {
      document.getElementById("user-name").textContent =
        user.name || user.email;
    }
    await loadWeeks();
    await loadMarginData();
  } catch (error) {
    console.error("Margin init error:", error);
    showError("Failed to load margin data");
  }
}

/**
 * Load margin page data
 */
async function loadMarginData() {
  showLoading(true);
  try {
    const week = weeksData.find((w) => w.week_id === currentWeekId);
    if (week) {
      document.getElementById("week-label").textContent = `Week ${week.label}`;
    }

    const [marginData, marginTrend] = await Promise.all([
      api.get(`/api/margin?week_id=${currentWeekId}`),
      api.get("/api/margin/trend?weeks=13"),
    ]);

    // Update KPIs
    document.getElementById("kpi-margin").textContent = api.formatPercent(
      marginData.overall_margin_percent || 0,
    );
    document.getElementById("kpi-margin-target").textContent = `Target: 30%`;
    document.getElementById("kpi-revenue").textContent = api.formatCurrency(
      marginData.total_revenue || 0,
    );
    document.getElementById("kpi-cost").textContent = api.formatCurrency(
      marginData.total_cost || 0,
    );

    // Render trend chart
    renderMarginTrendChart(marginTrend);

    // Update table
    updateMarginTable(marginData.by_product);

    showLoading(false);
  } catch (error) {
    console.error("Margin load error:", error);
    showError("Failed to load margin data");
    showLoading(false);
  }
}

/**
 * Update margin table
 */
function updateMarginTable(products) {
  const tbody = document.getElementById("margin-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  (products || []).forEach((p) => {
    const variance = (p.margin_percent || 0) - (p.target_margin || 30);
    const varianceClass =
      variance >= 0 ? "variance-positive" : "variance-negative";
    const row = document.createElement("tr");
    row.innerHTML = `
            <td>${p.product_group}</td>
            <td class="text-end">${api.formatCurrency(p.revenue || 0)}</td>
            <td class="text-end">${api.formatCurrency(p.cost || 0)}</td>
            <td class="text-end">${api.formatCurrency(p.margin || 0)}</td>
            <td class="text-end">${api.formatPercent(p.margin_percent || 0)}</td>
            <td class="text-end">${api.formatPercent(p.target_margin || 30)}</td>
            <td class="text-end ${varianceClass}">${variance >= 0 ? "+" : ""}${variance.toFixed(1)}%</td>
        `;
    tbody.appendChild(row);
  });

  if (!products || products.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="7" class="text-center text-muted">No margin data available</td></tr>';
  }
}

/**
 * Initialize Labor page
 */
async function initLabor() {
  try {
    const user = api.getUser();
    if (user) {
      document.getElementById("user-name").textContent =
        user.name || user.email;
    }
    await loadWeeks();
    await loadLaborData();
  } catch (error) {
    console.error("Labor init error:", error);
    showError("Failed to load labor data");
  }
}

/**
 * Set job filter and reload data
 */
function setJobFilter(filter) {
  currentJobFilter = filter;

  // Update button states
  document.getElementById('filter-all').classList.toggle('active', filter === 'all');
  document.getElementById('filter-wip').classList.toggle('active', filter === 'wip');
  document.getElementById('filter-completed').classList.toggle('active', filter === 'completed');

  // Reload data
  loadLaborData();
}

/**
 * Load labor page data
 */
async function loadLaborData() {
  showLoading(true);
  try {
    const week = weeksData.find((w) => w.week_id === currentWeekId);
    if (week) {
      document.getElementById("week-label").textContent = `Week ${week.label}`;
    }

    const laborData = await api.get(`/api/labor?week_id=${currentWeekId}&status=${currentJobFilter}`);

    // Update KPIs - uses LaborDtl_LaborHrs, LaborDtl_BurdenHrs from jt_zLaborDtl01
    document.getElementById("kpi-direct-labor").textContent =
      api.formatCurrency(laborData.total_direct_labor || 0);
    document.getElementById("kpi-labor-hours").textContent =
      `${parseFloat(laborData.total_labor_hours || 0).toFixed(1)} hours`;
    document.getElementById("kpi-burden").textContent = api.formatCurrency(
      laborData.total_burden || 0,
    );
    document.getElementById("kpi-burden-hours").textContent =
      `${parseFloat(laborData.total_burden_hours || 0).toFixed(1)} hours`;
    document.getElementById("kpi-total-labor").textContent = api.formatCurrency(
      laborData.total_labor_cost || 0,
    );
    document.getElementById("kpi-jobs").textContent = laborData.job_count || 0;

    // Render chart
    renderLaborChart(laborData.by_job);

    // Update table
    updateLaborTable(laborData.by_job);

    showLoading(false);
  } catch (error) {
    console.error("Labor load error:", error);
    showError("Failed to load labor data");
    showLoading(false);
  }
}

/**
 * Update labor table
 */
function updateLaborTable(jobs) {
  const tbody = document.getElementById("labor-table-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  (jobs || []).forEach((job) => {
    const statusBadge = job.job_closed
      ? '<span class="badge bg-secondary">Completed</span>'
      : '<span class="badge bg-success">WIP</span>';
    const laborHrs = parseFloat(job.labor_hours || 0).toFixed(1);
    const row = document.createElement("tr");
    row.innerHTML = `
            <td><a href="#" onclick="showJobDetail('${job.job_num}')">${job.job_num}</a></td>
            <td>${job.sales_order_num || "--"}</td>
            <td>${job.product_group || "--"}</td>
            <td>${statusBadge}</td>
            <td class="text-end">${laborHrs}</td>
            <td class="text-end">${api.formatCurrency(job.direct_labor || 0)}</td>
            <td class="text-end">${api.formatCurrency(job.burden || 0)}</td>
            <td class="text-end"><strong>${api.formatCurrency(job.total_labor || 0)}</strong></td>
        `;
    tbody.appendChild(row);
  });

  if (!jobs || jobs.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="8" class="text-center text-muted">No labor data available</td></tr>';
  }
}

/**
 * Render labor chart
 */
function renderLaborChart(jobs) {
  const chartDiv = document.getElementById("chart-labor");
  if (!chartDiv || !jobs || jobs.length === 0) return;

  const topJobs = jobs.slice(0, 10);
  const data = [
    {
      type: "bar",
      x: topJobs.map((j) => j.job_num),
      y: topJobs.map((j) => j.total_cost || 0),
      marker: { color: "#FF6600" },
    },
  ];

  const layout = {
    margin: { t: 20, b: 60, l: 80, r: 20 },
    xaxis: { title: "Job Number" },
    yaxis: { title: "Total Cost ($)", tickformat: "$,.0f" },
  };

  Plotly.newPlot(chartDiv, data, layout, { responsive: true });
}
