// KnowledgeLens - Evaluation Dashboard & Chart Script

document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('runEvalBtn');
    let evalData = null;

    if (runBtn) {
        runBtn.addEventListener('click', runEvaluation);
    }

    // Filter pills
    document.querySelectorAll('.filter-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            filterTable(pill.dataset.filter);
        });
    });

    function runEvaluation() {
        runBtn.disabled = true;
        runBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running 45 Questions...';
        window.showToast('Executing automated symbolic benchmark suite...', 'info');

        fetch('/api/eval/run')
            .then(r => r.json())
            .then(data => {
                runBtn.disabled = false;
                runBtn.innerHTML = '<i class="fa-solid fa-play"></i> Run Complete Benchmark';
                if (data.status === 'success') {
                    evalData = data.report;
                    renderReport(evalData);
                    window.showToast(`Benchmark Complete: ${evalData.accuracy}% Accuracy (${evalData.passed}/${evalData.total_questions} passed)`, 'success');
                } else {
                    window.showToast('Evaluation failed: ' + data.message, 'error');
                }
            })
            .catch(err => {
                runBtn.disabled = false;
                runBtn.innerHTML = '<i class="fa-solid fa-play"></i> Run Complete Benchmark';
                window.showToast('Evaluation error: ' + err, 'error');
            });
    }

    function renderReport(report) {
        // High-level metrics
        document.getElementById('metricAccuracy').textContent = report.accuracy + '%';
        document.getElementById('metricPassedCount').textContent = `${report.passed} / ${report.total_questions} passed (${report.failed} failed)`;
        document.getElementById('metricPrecRec').textContent = `${report.precision}% / ${report.recall}%`;
        document.getElementById('metricF1').textContent = `F1 Score: ${report.f1}%`;
        document.getElementById('metricRejection').textContent = report.rejection_correctness + '%';
        document.getElementById('metricLatency').textContent = report.avg_response_time_ms + ' ms';
        document.getElementById('metricCoverage').textContent = `Coverage: ${report.coverage}%`;

        // Ablation updates
        if (report.ablation_results) {
            const full = report.ablation_results['Full System'];
            const fuzzy = report.ablation_results['Fuzzy Matching OFF'];
            const rules = report.ablation_results['Inference Rules OFF'];

            if (full) document.getElementById('ablFullScore').textContent = full.accuracy + '%';
            if (fuzzy) {
                document.getElementById('ablFuzzyScore').textContent = fuzzy.accuracy + '%';
                document.getElementById('ablFuzzyDelta').textContent = fuzzy.delta;
            }
            if (rules) {
                document.getElementById('ablRulesScore').textContent = rules.accuracy + '%';
                document.getElementById('ablRulesDelta').textContent = rules.delta;
            }
        }

        // Error Analysis
        const errs = report.error_analysis || {};
        document.getElementById('errExtraction').textContent = errs['EXTRACTION_MISS'] || 0;
        document.getElementById('errEntity').textContent = errs['ENTITY_LINK_MISS'] || 0;
        document.getElementById('errRelation').textContent = errs['WRONG_RELATION'] || 0;
        document.getElementById('errReasoning').textContent = errs['REASONING_GAP'] || 0;

        // Render Type Bar Chart on Canvas
        renderCanvasBarChart(report.type_breakdown);

        // Render Detailed Results Table
        renderTable(report.question_results || []);
    }

    function renderCanvasBarChart(breakdown) {
        const canvas = document.getElementById('typeChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);

        const keys = Object.keys(breakdown || {});
        if (!keys.length) return;

        const barHeight = 18;
        const gap = 10;
        let startY = 15;

        keys.forEach(k => {
            const item = breakdown[k];
            const acc = item.accuracy || 0;
            const barW = (acc / 100) * (width - 150);

            // Label
            ctx.fillStyle = '#94a3b8';
            ctx.font = '10px Inter, sans-serif';
            ctx.fillText(k, 10, startY + 13);

            // Bar background
            ctx.fillStyle = '#334155';
            ctx.fillRect(130, startY, width - 150, barHeight);

            // Bar fill
            ctx.fillStyle = acc === 100 ? '#10b981' : (acc >= 75 ? '#3b82f6' : '#f59e0b');
            ctx.fillRect(130, startY, barW, barHeight);

            // Value text
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 9px Inter, sans-serif';
            ctx.fillText(`${acc}% (${item.passed}/${item.total})`, 135, startY + 12);

            startY += barHeight + gap;
        });
    }

    function renderTable(results) {
        const tbody = document.getElementById('evalTableBody');
        tbody.innerHTML = '';

        if (!results.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No benchmark results.</td></tr>';
            return;
        }

        results.forEach(r => {
            const tr = document.createElement('tr');
            tr.className = `eval-row ${r.passed ? 'row-pass' : 'row-fail'}`;
            tr.dataset.passed = r.passed ? 'true' : 'false';

            const badge = r.passed
                ? '<span class="badge badge-success"><i class="fa-solid fa-check"></i> PASS</span>'
                : `<span class="badge badge-danger"><i class="fa-solid fa-xmark"></i> FAIL</span><br><small class="text-muted">${r.error_category}</small>`;

            tr.innerHTML = `
                <td><code>${r.id}</code></td>
                <td><strong>${r.question}</strong></td>
                <td><small class="badge badge-secondary">${r.category}</small></td>
                <td><code>${r.expected_type}</code></td>
                <td><small class="text-muted">${r.technique}</small></td>
                <td>${badge}</td>
                <td style="font-size: 0.8rem; max-width: 320px;">${r.actual_answer}</td>
                <td>${r.time_ms} ms</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function filterTable(filterMode) {
        document.querySelectorAll('.eval-row').forEach(row => {
            const isPass = row.dataset.passed === 'true';
            if (filterMode === 'all') {
                row.style.display = '';
            } else if (filterMode === 'pass') {
                row.style.display = isPass ? '' : 'none';
            } else if (filterMode === 'fail') {
                row.style.display = !isPass ? '' : 'none';
            }
        });
    }

    // Auto-run benchmark on first page view if not already ran
    runEvaluation();
});
