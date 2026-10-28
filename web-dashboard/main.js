import { Chart, registerables } from 'chart.js';
import { KPI_DATA, MONTHLY_DATA, CATEGORY_DATA, REGIONAL_DATA, DELIVERY_DATA, ML_METRICS } from './data.js';

Chart.register(...registerables);

// Chart.js defaults to match the page (light paper, muted ink)
Chart.defaults.color = '#6b6a63';
Chart.defaults.font.family = "'IBM Plex Sans', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.tooltip.backgroundColor = '#1f1f1c';
Chart.defaults.plugins.tooltip.titleColor = '#f7f5f0';
Chart.defaults.plugins.tooltip.bodyColor = '#e6e2d8';
Chart.defaults.plugins.tooltip.padding = 8;
Chart.defaults.plugins.tooltip.cornerRadius = 2;
Chart.defaults.plugins.legend.labels.boxWidth = 12;
Chart.defaults.plugins.legend.labels.boxHeight = 12;
Chart.defaults.borderColor = 'rgba(31, 31, 28, 0.08)';
Chart.defaults.elements.bar.borderRadius = 0;
Chart.defaults.elements.point.radius = 0;
Chart.defaults.elements.point.hoverRadius = 4;

const C = {
  ink: '#1f1f1c',
  blue: '#3d5a80',
  rust: '#b4532a',
  green: '#4f7a4a',
  ochre: '#b8862f',
  red: '#a63d32',
  plum: '#7a5c7e',
};

// Formatters
const formatCurrency = (val) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
const formatNumber = (val) => new Intl.NumberFormat('en-US').format(val);

// Tab Navigation
function setupTabs() {
  const navBtns = document.querySelectorAll('.nav-item');
  const panes = document.querySelectorAll('.tab-pane');

  navBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      navBtns.forEach((b) => b.classList.remove('active'));
      panes.forEach((p) => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
      }
    });
  });
}

// Chart 1: Overview Monthly Trends
let overviewChartInstance = null;
function initOverviewTrendChart(mode = 'combined') {
  const ctx = document.getElementById('overviewTrendChart');
  if (!ctx) return;

  if (overviewChartInstance) {
    overviewChartInstance.destroy();
  }

  const labels = MONTHLY_DATA.map((d) => d.order_year_month);
  const sales = MONTHLY_DATA.map((d) => d.total_sales);
  const profit = MONTHLY_DATA.map((d) => d.total_profit);
  const margin = MONTHLY_DATA.map((d) => d.profit_margin_pct);

  if (mode === 'combined') {
    overviewChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Total Sales ($)',
            data: sales,
            backgroundColor: C.blue,
            borderWidth: 0,
            yAxisID: 'y',
          },
          {
            type: 'line',
            label: 'Net Profit ($)',
            data: profit,
            borderColor: C.green,
            backgroundColor: 'transparent',
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 2,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
          x: { grid: { display: false }, ticks: { maxRotation: 45, maxTicksLimit: 14 } },
          y: {
            position: 'left',
            ticks: { callback: (val) => `$${(val / 1e6).toFixed(1)}M` },
            title: { display: true, text: 'Gross Sales' },
          },
          y1: {
            position: 'right',
            grid: { display: false },
            ticks: { callback: (val) => `$${(val / 1e3).toFixed(0)}k` },
            title: { display: true, text: 'Net Profit' },
          },
        },
      },
    });
  } else {
    overviewChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Profit Margin %',
            data: margin,
            borderColor: C.ochre,
            backgroundColor: 'rgba(184, 134, 47, 0.12)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false }, ticks: { maxRotation: 45, maxTicksLimit: 14 } },
          y: {
            ticks: { callback: (val) => `${val}%` },
            title: { display: true, text: 'Margin (%)' },
          },
        },
      },
    });
  }
}

// Chart 2: Overview Shipping Lateness
function initOverviewShippingChart() {
  const ctx = document.getElementById('overviewShippingChart');
  if (!ctx) return;

  const modes = DELIVERY_DATA.filter((d) => d.dimension === 'shipping_mode');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: modes.map((m) => m.segment),
      datasets: [
        {
          label: 'Late Delivery Rate %',
          data: modes.map((m) => m.late_rate_pct),
          backgroundColor: modes.map((m) => (m.late_rate_pct >= 50 ? C.red : '#b9b4a8')),
        },
      ],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          max: 100,
          ticks: { callback: (val) => `${val}%` },
        },
        y: { grid: { display: false } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `Late Rate: ${ctx.raw}% (${modes[ctx.dataIndex].late_shipments.toLocaleString()} shipments)`,
          },
        },
      },
    },
  });
}

// Chart 3: Overview Region Doughnut
function initOverviewRegionDoughnut() {
  const ctx = document.getElementById('overviewRegionDoughnut');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: REGIONAL_DATA.map((r) => r.market),
      datasets: [
        {
          data: REGIONAL_DATA.map((r) => r.total_sales),
          backgroundColor: [C.blue, C.rust, C.green, C.ochre, C.plum],
          borderWidth: 2,
          borderColor: '#fffefb',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right' },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${formatCurrency(ctx.raw)}`,
          },
        },
      },
      cutout: '60%',
    },
  });
}

// Chart 4: Full 37-Month Timeline
function initFullTrendsChart() {
  const ctx = document.getElementById('fullTrendsChart');
  if (!ctx) return;

  const labels = MONTHLY_DATA.map((d) => d.order_year_month);
  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Sales Revenue ($)',
          data: MONTHLY_DATA.map((d) => d.total_sales),
          borderColor: C.blue,
          backgroundColor: 'rgba(61, 90, 128, 0.08)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          yAxisID: 'y',
        },
        {
          label: 'Distinct Orders',
          data: MONTHLY_DATA.map((d) => d.order_count),
          borderColor: C.ink,
          backgroundColor: 'transparent',
          borderDash: [4, 3],
          tension: 0.35,
          borderWidth: 2,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { ticks: { maxRotation: 45, maxTicksLimit: 18 } },
        y: {
          position: 'left',
          ticks: { callback: (val) => `$${(val / 1e6).toFixed(1)}M` },
        },
        y1: {
          position: 'right',
          grid: { display: false },
          ticks: { callback: (val) => `${val.toLocaleString()} orders` },
        },
      },
    },
  });
}

// Chart 5: Category Performance Bar
function initCategorySalesChart() {
  const ctx = document.getElementById('categorySalesChart');
  if (!ctx) return;

  const top10 = CATEGORY_DATA.slice(0, 10);
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top10.map((c) => c.category_name),
      datasets: [
        {
          label: 'Sales (USD)',
          data: top10.map((c) => c.total_sales),
          backgroundColor: C.blue,
        },
      ],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { callback: (val) => `$${(val / 1e6).toFixed(1)}M` } },
        y: { grid: { display: false } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Sales: ${formatCurrency(ctx.raw)} | Margin: ${top10[ctx.dataIndex].profit_margin_pct}%`,
          },
        },
      },
    },
  });
}

// Chart 6: Delivery Mode SLAs
function initDeliveryModeChart() {
  const ctx = document.getElementById('deliveryModeChart');
  if (!ctx) return;

  const modes = DELIVERY_DATA.filter((d) => d.dimension === 'shipping_mode');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: modes.map((m) => m.segment),
      datasets: [
        {
          label: 'Total Shipments',
          data: modes.map((m) => m.total_shipments),
          backgroundColor: '#c9cfd8',
          yAxisID: 'y',
        },
        {
          type: 'line',
          label: 'Late Rate %',
          data: modes.map((m) => m.late_rate_pct),
          borderColor: C.red,
          borderWidth: 3,
          pointRadius: 4,
          pointBackgroundColor: C.red,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { position: 'left', ticks: { callback: (val) => `${(val / 1e3).toFixed(0)}k` } },
        y1: {
          position: 'right',
          max: 100,
          grid: { display: false },
          ticks: { callback: (val) => `${val}%` },
        },
      },
    },
  });
}

// Chart 7: Delivery Duration
function initDeliveryDurationChart() {
  const ctx = document.getElementById('deliveryDurationChart');
  if (!ctx) return;

  const modes = DELIVERY_DATA.filter((d) => d.dimension === 'shipping_mode');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: modes.map((m) => m.segment),
      datasets: [
        {
          label: 'Scheduled Days',
          data: modes.map((m) => m.avg_scheduled_days),
          backgroundColor: '#b9b4a8',
        },
        {
          label: 'Actual Days Taken',
          data: modes.map((m) => m.avg_actual_days),
          backgroundColor: C.red,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { title: { display: true, text: 'Average Days' } },
      },
    },
  });
}

// Chart 8: Regional Bar Chart
function initRegionalBarChart() {
  const ctx = document.getElementById('regionalBarChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: REGIONAL_DATA.map((r) => r.market),
      datasets: [
        {
          label: 'Total Sales ($)',
          data: REGIONAL_DATA.map((r) => r.total_sales),
          backgroundColor: C.blue,
          yAxisID: 'y',
        },
        {
          type: 'line',
          label: 'Profit Margin %',
          data: REGIONAL_DATA.map((r) => r.profit_margin_pct),
          borderColor: C.green,
          borderWidth: 2.5,
          pointRadius: 5,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { ticks: { callback: (val) => `$${(val / 1e6).toFixed(1)}M` } },
        y1: {
          position: 'right',
          grid: { display: false },
          ticks: { callback: (val) => `${val}%` },
        },
      },
    },
  });
}

// Render Monthly Data Table
function renderMonthlyTable(searchTerm = '') {
  const tbody = document.getElementById('monthly-table-body');
  if (!tbody) return;

  const filtered = MONTHLY_DATA.filter((d) => d.order_year_month.toLowerCase().includes(searchTerm.toLowerCase()));

  tbody.innerHTML = filtered
    .map((row) => {
      const margin = row.profit_margin_pct;
      const statusBadge =
        margin >= 4
          ? '<span class="tag-healthy">Healthy</span>'
          : margin >= 2
          ? '<span class="tag-medium">Average</span>'
          : '<span class="tag-critical">Low Margin</span>';

      return `
      <tr>
        <td><strong>${row.order_year_month}</strong></td>
        <td>${formatCurrency(row.total_sales)}</td>
        <td>${formatCurrency(row.total_item_revenue)}</td>
        <td>${formatNumber(row.order_count)}</td>
        <td>${formatCurrency(row.total_profit)}</td>
        <td><strong>${margin}%</strong></td>
        <td>${statusBadge}</td>
      </tr>
    `;
    })
    .join('');
}

// Render Category Data Table
function renderCategoryTable(searchTerm = '') {
  const tbody = document.getElementById('category-table-body');
  if (!tbody) return;

  const filtered = CATEGORY_DATA.filter((c) => c.category_name.toLowerCase().includes(searchTerm.toLowerCase()));

  tbody.innerHTML = filtered
    .map((cat) => {
      const margin = cat.profit_margin_pct;
      const marginBadge =
        margin >= 10
          ? '<span class="badge-success">High Margin (>10%)</span>'
          : margin >= 3
          ? '<span class="badge-warning">Standard (3-10%)</span>'
          : '<span class="badge-danger">Thin Margin (<3%)</span>';

      return `
      <tr>
        <td><strong>${cat.category_name}</strong></td>
        <td>${formatCurrency(cat.total_sales)}</td>
        <td>${formatCurrency(cat.total_profit)}</td>
        <td>${formatNumber(cat.order_item_count)}</td>
        <td><strong>${margin}%</strong></td>
        <td>${marginBadge}</td>
      </tr>
    `;
    })
    .join('');
}

// Late-delivery risk estimator
function setupRiskSimulator() {
  const predictBtn = document.getElementById('btn-predict-risk');
  const scoreNum = document.getElementById('risk-percent-num');
  const levelTag = document.getElementById('risk-level-tag');
  const advisoryText = document.getElementById('risk-advisory-text');
  const circle = document.getElementById('risk-score-display');

  if (!predictBtn) return;

  predictBtn.addEventListener('click', () => {
    const mode = document.getElementById('sim-shipping-mode').value;
    const market = document.getElementById('sim-market').value;
    const price = parseFloat(document.getElementById('sim-price').value) || 100;
    const discount = parseFloat(document.getElementById('sim-discount').value) || 10;

    // Simulation calculation anchored on empirical Logistic Regression features
    let baseProbability = 0.38;

    if (mode === 'First Class') baseProbability += 0.57; // 95%
    else if (mode === 'Second Class') baseProbability += 0.38; // 76%
    else if (mode === 'Same Day') baseProbability += 0.08; // 45%
    else if (mode === 'Standard Class') baseProbability -= 0.05; // 38%

    if (discount > 25) baseProbability += 0.04;
    if (price > 400) baseProbability += 0.02;

    const probPercent = Math.min(99, Math.max(5, Math.round(baseProbability * 100)));

    scoreNum.textContent = `${probPercent}%`;

    if (probPercent >= 75) {
      circle.dataset.level = 'high';
      levelTag.className = 'risk-level-tag tag-critical';
      levelTag.textContent = 'High risk';
      advisoryText.innerHTML = `<strong>${mode}</strong> misses its promised date more than 75% of the time. For orders to ${market}, it's worth telling the customer up front or switching to Standard Class.`;
    } else if (probPercent >= 45) {
      circle.dataset.level = 'medium';
      levelTag.className = 'risk-level-tag tag-medium';
      levelTag.textContent = 'Medium risk';
      advisoryText.innerHTML = `<strong>${mode}</strong> to ${market} is roughly a coin flip. Shipping before the daily cut-off helps.`;
    } else {
      circle.dataset.level = 'low';
      levelTag.className = 'risk-level-tag tag-healthy';
      levelTag.textContent = 'Low risk';
      advisoryText.innerHTML = `<strong>${mode}</strong> to ${market} usually arrives on time. Nothing unusual here.`;
    }
  });
}

// Chart toggle buttons
function setupChartToggles() {
  const btnRev = document.getElementById('btn-toggle-revenue');
  const btnMargin = document.getElementById('btn-toggle-margin');

  if (btnRev && btnMargin) {
    btnRev.addEventListener('click', () => {
      btnRev.classList.add('active');
      btnMargin.classList.remove('active');
      initOverviewTrendChart('combined');
    });

    btnMargin.addEventListener('click', () => {
      btnMargin.classList.add('active');
      btnRev.classList.remove('active');
      initOverviewTrendChart('margin');
    });
  }
}

// Search filters
function setupSearchFilters() {
  const monthlySearch = document.getElementById('monthly-search');
  if (monthlySearch) {
    monthlySearch.addEventListener('input', (e) => {
      renderMonthlyTable(e.target.value);
    });
  }

  const categorySearch = document.getElementById('category-search');
  if (categorySearch) {
    categorySearch.addEventListener('input', (e) => {
      renderCategoryTable(e.target.value);
    });
  }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupChartToggles();
  setupSearchFilters();
  setupRiskSimulator();

  initOverviewTrendChart('combined');
  initOverviewShippingChart();
  initOverviewRegionDoughnut();

  initFullTrendsChart();
  initCategorySalesChart();
  initDeliveryModeChart();
  initDeliveryDurationChart();
  initRegionalBarChart();

  renderMonthlyTable();
  renderCategoryTable();
});
