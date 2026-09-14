let rawData = [];
let chartInstance = null;

// Parse the aggregated CSV file from data/ directory with cache-busting
Papa.parse("data/texas_permit_summary.csv?v=" + new Date().getTime(), {
  download: true,
  header: true,
  skipEmptyLines: true,
  complete: function(results) {
    rawData = results.data;
    console.log("Parsed CSV Data successfully:", rawData);
    renderChart();
  }
});

function renderChart() {
  const selectedScope = document.getElementById('scopeFilter').value;
  
  // Filter dataset by selected scope
  let filtered = rawData.filter(d => d.work_scope === selectedScope);
  
  // Fallback: If no records exist for selected scope, render available records
  if (filtered.length === 0 && rawData.length > 0) {
    console.warn(`No data found for scope: ${selectedScope}. Showing fallback dataset.`);
    filtered = rawData;
  }

  const cities = [...new Set(filtered.map(d => d.city))].filter(Boolean);

  const singleFamilyData = cities.map(city => {
    const record = filtered.find(d => d.city === city && d.project_type === 'Single Family');
    return record ? parseFloat(record.median_review_days || 0) : 0;
  });

  const multiFamilyData = cities.map(city => {
    const record = filtered.find(d => d.city === city && d.project_type === 'Multifamily');
    return record ? parseFloat(record.median_review_days || 0) : 0;
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

function updateChart() {
  renderChart();
}
