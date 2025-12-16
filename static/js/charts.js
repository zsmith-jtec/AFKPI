/**
 * AFKPI Chart Rendering
 * Uses Plotly.js with JTEC brand colors
 */

// JTEC Brand Colors
const COLORS = {
    orange: '#FF6600',
    orangeLight: '#ff8533',
    black: '#1a1a1a',
    gray: '#6c757d',
    success: '#4CAF50',
    danger: '#f44336'
};

// Common Plotly layout settings
const commonLayout = {
    font: {
        family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { t: 30, r: 20, b: 40, l: 60 }
};

const commonConfig = {
    responsive: true,
    displayModeBar: false
};

/**
 * Render Revenue by Product Group horizontal bar chart
 */
function renderRevenueChart(byProduct) {
    if (!byProduct || byProduct.length === 0) {
        document.getElementById('chart-revenue').innerHTML =
            '<p class="text-center text-muted py-5">No revenue data available</p>';
        return;
    }

    // Sort by outbound revenue descending
    const sorted = [...byProduct].sort((a, b) =>
        parseFloat(b.outbound || 0) - parseFloat(a.outbound || 0)
    );

    const data = [{
        type: 'bar',
        orientation: 'h',
        y: sorted.map(d => d.product_group),
        x: sorted.map(d => parseFloat(d.outbound || 0)),
        marker: {
            color: COLORS.orange
        },
        hovertemplate: '%{y}<br>$%{x:,.0f}<extra></extra>'
    }];

    const layout = {
        ...commonLayout,
        margin: { ...commonLayout.margin, l: 120 },
        xaxis: {
            title: 'Revenue ($)',
            tickformat: '$,.0f',
            gridcolor: '#e0e0e0'
        },
        yaxis: {
            automargin: true
        }
    };

    Plotly.newPlot('chart-revenue', data, layout, commonConfig);
}

/**
 * Render Margin Trend line chart
 */
function renderMarginTrendChart(trendData) {
    if (!trendData || trendData.length === 0) {
        document.getElementById('chart-margin').innerHTML =
            '<p class="text-center text-muted py-5">No trend data available</p>';
        return;
    }

    const labels = trendData.map(d => d.label);
    const margins = trendData.map(d => parseFloat(d.margin_percent || 0));

    // Actual margin line
    const actualTrace = {
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Actual Margin',
        x: labels,
        y: margins,
        line: {
            color: COLORS.orange,
            width: 3
        },
        marker: {
            size: 8,
            color: COLORS.orange
        },
        hovertemplate: '%{x}<br>%{y:.1f}%<extra></extra>'
    };

    // Target line (30%)
    const targetTrace = {
        type: 'scatter',
        mode: 'lines',
        name: 'Target (30%)',
        x: labels,
        y: labels.map(() => 30),
        line: {
            color: COLORS.gray,
            width: 2,
            dash: 'dash'
        },
        hoverinfo: 'skip'
    };

    const layout = {
        ...commonLayout,
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.15
        },
        xaxis: {
            tickangle: -45,
            gridcolor: '#e0e0e0'
        },
        yaxis: {
            title: 'Margin %',
            ticksuffix: '%',
            gridcolor: '#e0e0e0',
            range: [0, Math.max(40, Math.max(...margins) + 5)]
        }
    };

    Plotly.newPlot('chart-margin', [actualTrace, targetTrace], layout, commonConfig);
}

/**
 * Render Margin by Product Group bar chart (for margin page)
 */
function renderMarginByProductChart(byProduct) {
    if (!byProduct || byProduct.length === 0) {
        return;
    }

    const sorted = [...byProduct].sort((a, b) =>
        parseFloat(b.margin_percent || 0) - parseFloat(a.margin_percent || 0)
    );

    // Color bars based on target variance
    const colors = sorted.map(d => {
        const variance = parseFloat(d.variance || 0);
        return variance >= 0 ? COLORS.success : COLORS.danger;
    });

    const data = [{
        type: 'bar',
        x: sorted.map(d => d.product_group),
        y: sorted.map(d => parseFloat(d.margin_percent || 0)),
        marker: {
            color: colors
        },
        hovertemplate: '%{x}<br>%{y:.1f}%<extra></extra>'
    }];

    const layout = {
        ...commonLayout,
        xaxis: {
            tickangle: -45
        },
        yaxis: {
            title: 'Margin %',
            ticksuffix: '%',
            gridcolor: '#e0e0e0'
        },
        shapes: [{
            type: 'line',
            x0: -0.5,
            x1: sorted.length - 0.5,
            y0: 30,
            y1: 30,
            line: {
                color: COLORS.gray,
                width: 2,
                dash: 'dash'
            }
        }]
    };

    Plotly.newPlot('chart-margin-products', data, layout, commonConfig);
}
