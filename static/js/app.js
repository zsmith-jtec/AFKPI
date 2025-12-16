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
 * Load available weeks into dropdown
 */
async function loadWeeks() {
  const weeks = await api.get("/api/weeks");
  weeksData = weeks;

  const selector = document.getElementById("week-selector");
  selector.innerHTML = "";

  weeks.forEach((week, index) => {
    const option = document.createElement("option");
    option.value = week.week_id;
    option.textContent = week.label;
    if (index === 0) {
      option.selected = true;
      currentWeekId = week.week_id;
    }
    selector.appendChild(option);
  });

  // Add change listener - detect which page we're on
  selector.addEventListener("change", function () {
    currentWeekId = parseInt(this.value);
    // Call appropriate load function based on current page
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
  });
}

/**
 * Load all dashboard data
 */
async function loadDashboardData() {
  showLoading(true);

  try {
    // Update week label
    const week = weeksData.find((w) => w.week_id === currentWeekId);
    if (week) {
      document.getElementById("week-label").textContent = `Week ${week.label}`;
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
    const row = document.createElement("tr");
    row.innerHTML = `
            <td><a href="#" onclick="showJobDetail('${job.job_num}')">${job.job_num}</a></td>
            <td>${job.sales_order_num || "--"}</td>
            <td>${job.product_group || "--"}</td>
            <td class="text-end">${api.formatCurrency(job.direct_labor)}</td>
            <td class="text-end">${api.formatCurrency(job.burden)}</td>
            <td class="text-end"><strong>${api.formatCurrency(job.total_cost)}</strong></td>
        `;
    tbody.appendChild(row);
  });

  if (topJobs.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="6" class="text-center text-muted">No job data available</td></tr>';
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
 * Load labor page data
 */
async function loadLaborData() {
  showLoading(true);
  try {
    const week = weeksData.find((w) => w.week_id === currentWeekId);
    if (week) {
      document.getElementById("week-label").textContent = `Week ${week.label}`;
    }

    const laborData = await api.get(`/api/labor?week_id=${currentWeekId}`);

    // Update KPIs
    document.getElementById("kpi-direct-labor").textContent =
      api.formatCurrency(laborData.total_direct_labor || 0);
    document.getElementById("kpi-labor-hours").textContent =
      `${(laborData.total_labor_hours || 0).toFixed(1)} hours`;
    document.getElementById("kpi-burden").textContent = api.formatCurrency(
      laborData.total_burden || 0,
    );
    document.getElementById("kpi-burden-hours").textContent =
      `${(laborData.total_burden_hours || 0).toFixed(1)} hours`;
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
    const row = document.createElement("tr");
    row.innerHTML = `
            <td><a href="#" onclick="showJobDetail('${job.job_num}')">${job.job_num}</a></td>
            <td>${job.sales_order_num || "--"}</td>
            <td>${job.product_group || "--"}</td>
            <td class="text-end">${(job.labor_hours || 0).toFixed(1)}</td>
            <td class="text-end">${api.formatCurrency(job.direct_labor || 0)}</td>
            <td class="text-end">${api.formatCurrency(job.burden || 0)}</td>
            <td class="text-end"><strong>${api.formatCurrency(job.total_cost || 0)}</strong></td>
        `;
    tbody.appendChild(row);
  });

  if (!jobs || jobs.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="7" class="text-center text-muted">No labor data available</td></tr>';
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
