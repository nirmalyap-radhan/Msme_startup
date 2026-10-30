/**
 * Udyog Sathi Interactive Data Visualizations
 * Powered by Chart.js (UMD)
 * Responsive, accessible, theme-aware (Light/Dark), and multilingual.
 */

class ChartsController {
  constructor() {
    this.charts = {};
    this.init();
  }

  init() {
    // Wait for DOM and Chart library
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }

    // Listen for theme changes & language changes
    window.addEventListener('languageChanged', () => this.renderAllCharts());
  }

  setup() {
    if (typeof Chart === 'undefined') {
      console.warn('Chart.js not yet loaded, retrying...');
      setTimeout(() => this.setup(), 500);
      return;
    }
    this.renderAllCharts();
  }

  getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      textColor: isDark ? '#cbd5e1' : '#475569',
      gridColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(15, 23, 42, 0.06)',
      tooltipBg: isDark ? '#112240' : '#0c1e3d',
      tooltipText: '#ffffff',
      primaryBlue: '#1366d9',
      gold: '#f59e0b',
      green: '#10b981',
      orange: '#ea580c',
      purple: '#8b5cf6',
      teal: '#0d9488'
    };
  }

  renderAllCharts() {
    if (typeof Chart === 'undefined') return;
    this.renderSectorChart();
    this.renderJurisdictionChart();
    this.renderIncentiveTypeChart();
  }

  renderSectorChart() {
    const canvas = document.getElementById('chartSectorDistribution');
    if (!canvas) return;

    if (this.charts.sector) {
      this.charts.sector.destroy();
    }

    const t = (k, fb) => (window.i18n ? window.i18n.t(k, fb) : fb);
    const colors = this.getThemeColors();

    const labels = [
      t('cat_mfg', 'Manufacturing'),
      t('cat_agro', 'Agro & Food Processing'),
      t('cat_tech', 'Technology & IT'),
      t('cat_services', 'Commercial Services'),
      t('cat_handlooms', 'Handloom & Handicrafts'),
      t('cat_green', 'Green & Renewable')
    ];

    const data = [38, 26, 22, 19, 15, 11];

    this.charts.sector = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: t('chart_sector_title', 'Schemes Available'),
          data: data,
          backgroundColor: [
            colors.primaryBlue,
            colors.green,
            colors.purple,
            colors.gold,
            colors.orange,
            colors.teal
          ],
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            padding: 10,
            cornerRadius: 6
          }
        },
        scales: {
          x: {
            ticks: { color: colors.textColor, font: { size: 11, weight: 600 } },
            grid: { display: false }
          },
          y: {
            ticks: { color: colors.textColor, font: { size: 11 } },
            grid: { color: colors.gridColor }
          }
        }
      }
    });
  }

  renderJurisdictionChart() {
    const canvas = document.getElementById('chartJurisdictionSplit');
    if (!canvas) return;

    if (this.charts.jurisdiction) {
      this.charts.jurisdiction.destroy();
    }

    const t = (k, fb) => (window.i18n ? window.i18n.t(k, fb) : fb);
    const colors = this.getThemeColors();

    const labels = [
      t('filter_odisha_only', 'Government of Odisha'),
      t('filter_central_only', 'Central Government'),
      t('cat_bank_product', 'Public Sector Bank Facilities')
    ];

    this.charts.jurisdiction = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: [58, 28, 14],
          backgroundColor: [
            '#0c1e3d',
            '#f59e0b',
            '#1366d9'
          ],
          borderColor: document.documentElement.getAttribute('data-theme') === 'dark' ? '#0f1d36' : '#ffffff',
          borderWidth: 3,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: colors.textColor,
              font: { size: 11, weight: 600 },
              padding: 14,
              boxWidth: 14
            }
          },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            padding: 10,
            cornerRadius: 6,
            callbacks: {
              label: function(context) {
                return ` ${context.label}: ${context.parsed}% of Scheme Portfolio`;
              }
            }
          }
        },
        cutout: '68%'
      }
    });
  }

  renderIncentiveTypeChart() {
    const canvas = document.getElementById('chartIncentiveTypes');
    if (!canvas) return;

    if (this.charts.incentive) {
      this.charts.incentive.destroy();
    }

    const t = (k, fb) => (window.i18n ? window.i18n.t(k, fb) : fb);
    const colors = this.getThemeColors();

    const labels = [
      'Capital Investment Subsidy (CIS)',
      'Interest Subvention (5%-6%)',
      'Collateral-Free Credit Guarantee',
      'Patent & Trade Mark Reimbursement',
      'Power Tariff Concession & Stamp Duty'
    ];

    this.charts.incentive = new Chart(canvas, {
      type: 'bar',
      indexAxis: 'y',
      data: {
        labels: labels,
        datasets: [{
          label: 'Coverage Intensity',
          data: [35, 25, 20, 12, 8],
          backgroundColor: '#10b981',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            padding: 10,
            cornerRadius: 6
          }
        },
        scales: {
          x: {
            ticks: { color: colors.textColor, font: { size: 11 } },
            grid: { color: colors.gridColor }
          },
          y: {
            ticks: { color: colors.textColor, font: { size: 11, weight: 600 } },
            grid: { display: false }
          }
        }
      }
    });
  }
}

// Global initialization
window.chartsController = new ChartsController();
window.renderAllCharts = () => window.chartsController.renderAllCharts();
