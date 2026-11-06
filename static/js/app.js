(function () {
  'use strict';

  const quickForm = document.getElementById('quickMetricForm');
  if (quickForm) {
    quickForm.addEventListener('submit', function (event) {
      const serverId = document.getElementById('serverSelect').value;
      if (!serverId) {
        event.preventDefault();
        window.alert('Please select a server first.');
        return;
      }
      quickForm.action = quickForm.dataset.baseUrl + serverId + '/metric/';
    });
  }

  function drawLineChart(canvas, labels, series) {
    if (!canvas || !canvas.getContext) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 640;
    const height = canvas.clientHeight || 230;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const pad = { top: 14, right: 16, bottom: 30, left: 34 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;
    const maxValue = Math.max(100, ...series.flatMap(item => item.values));
    const minValue = 0;
    ctx.font = '11px Inter, system-ui, sans-serif';
    ctx.fillStyle = '#8792a5';
    ctx.strokeStyle = '#e9edf3';
    ctx.lineWidth = 1;

    [0, 25, 50, 75, 100].forEach(value => {
      const y = pad.top + plotH - (value / maxValue) * plotH;
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke();
      ctx.fillText(String(value), 5, y + 4);
    });

    labels.forEach((label, index) => {
      if (labels.length > 7 && index % Math.ceil(labels.length / 6) !== 0 && index !== labels.length - 1) return;
      const x = pad.left + (labels.length <= 1 ? 0 : index / (labels.length - 1)) * plotW;
      ctx.fillStyle = '#8792a5';
      ctx.fillText(String(label), x - 15, height - 8);
    });

    series.forEach(item => {
      if (!item.values.length) return;
      ctx.beginPath();
      item.values.forEach((value, index) => {
        const x = pad.left + (item.values.length <= 1 ? 0 : index / (item.values.length - 1)) * plotW;
        const y = pad.top + plotH - (Math.max(minValue, Math.min(maxValue, value)) / maxValue) * plotH;
        if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = item.color; ctx.lineWidth = 2.5; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
      item.values.forEach((value, index) => {
        const x = pad.left + (item.values.length <= 1 ? 0 : index / (item.values.length - 1)) * plotW;
        const y = pad.top + plotH - (Math.max(minValue, Math.min(maxValue, value)) / maxValue) * plotH;
        ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fillStyle = item.color; ctx.fill();
      });
    });
  }

  function renderChart() {
    const canvas = document.getElementById('workloadChart');
    const data = window.cloudPilotChartData;
    if (!canvas || !data) return;
    drawLineChart(canvas, data.labels || [], [
      { values: data.cpu || [], color: '#4f7df3' },
      { values: data.memory || [], color: '#9b75e8' }
    ]);
  }
  document.addEventListener('DOMContentLoaded', renderChart);
  window.addEventListener('resize', renderChart);
})();
