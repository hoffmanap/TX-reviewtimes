let rawData = [];
let chartInstance = null;

// Parse the output aggregated CSV from data/ directory
Papa.parse("data/texas_permit_summary.csv", {
  download: true,
  header: true,
  complete: function(results) {
    rawData = results.data;
    renderChart();
  }
});

function renderChart() {
  const selectedScope = document.getElementById('scopeFilter').value;
  const filtered = rawData.filter(d => d.work_scope === selectedScope);
  const cities = [...new Set(filtered.map(d => d.city))].filter(Boolean);

  const singleFamilyData = cities.map(city => {
    const record = filtered.find(d => d.city === city && d.project_type === 'Single Family');
    return record ? parseFloat(record.median_review_days) : 0;
  });

  const multiFamilyData = cities.map(city => {
    const record = filtered.find(d => d.city === city && d.project_type === 'Multifamily');
    return record ? parseFloat(record.median_review_days) : 0;
  });

  const ctx = document.getElementById('permitChart').getContext('2d');
  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: cities,
      datasets: [
        {
          label: 'Single Family (Median Days)',
          data: singleFamilyData,
          backgroundColor: 'rgba(54, 162, 235, 0.75)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        },
        {
          label: 'Multifamily (Median Days)',
          data: multiFamilyData,
          backgroundColor: 'rgba(255, 99, 132, 0.75)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Median Review Duration (Days)' }
        }
      }
    }
  });
}
