// KnowledgeLens - Knowledge Graph Visualization with Vis.js & Canvas Fallback

window.kgNetworkInstance = null;
let graphNodesDataset = null;
let graphEdgesDataset = null;
let rawGraphData = null;
let physicsEnabled = true;

window.initKnowledgeGraph = function(graphData) {
    rawGraphData = graphData;
    const container = document.getElementById('kgNetwork');
    const canvasFallback = document.getElementById('kgCanvasFallback');
    if (!container) return;

    // Check if Vis.js is available
    if (typeof vis !== 'undefined') {
        container.classList.remove('hidden');
        if (canvasFallback) canvasFallback.classList.add('hidden');
        initVisJsGraph(container, graphData);
    } else {
        // Fallback to pure HTML5 Canvas Force-Directed Graph (100% offline)
        container.classList.add('hidden');
        if (canvasFallback) {
            canvasFallback.classList.remove('hidden');
            initCanvasGraphFallback(canvasFallback, graphData);
        }
    }
};

function initVisJsGraph(container, graphData) {
    graphNodesDataset = new vis.DataSet(graphData.nodes || []);
    graphEdgesDataset = new vis.DataSet(graphData.edges || []);

    const data = {
        nodes: graphNodesDataset,
        edges: graphEdgesDataset
    };

    const options = {
        nodes: {
            font: { color: '#ffffff', size: 12, face: 'Inter, sans-serif' },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            color: { color: '#64748b', highlight: '#3b82f6' },
            font: { color: '#94a3b8', size: 10, strokeWidth: 0 },
            smooth: { type: 'continuous' }
        },
        physics: {
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -38,
                centralGravity: 0.005,
                springLength: 80,
                springConstant: 0.18
            },
            stabilization: { iterations: 120 }
        },
        interaction: {
            hover: true,
            tooltipDelay: 150
        }
    };

    window.kgNetworkInstance = new vis.Network(container, data, options);

    // Node click handler
    window.kgNetworkInstance.on('click', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            showNodeDetails(nodeId);
        } else {
            hideNodeDetails();
        }
    });

    // Toolbar buttons
    const resetBtn = document.getElementById('resetZoomBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (window.kgNetworkInstance) window.kgNetworkInstance.fit();
        });
    }

    const togglePhysicsBtn = document.getElementById('togglePhysicsBtn');
    if (togglePhysicsBtn) {
        togglePhysicsBtn.addEventListener('click', () => {
            physicsEnabled = !physicsEnabled;
            window.kgNetworkInstance.setOptions({ physics: { enabled: physicsEnabled } });
            window.showToast(`Graph Physics: ${physicsEnabled ? 'Enabled' : 'Paused'}`);
        });
    }

    const closeDrawerBtn = document.getElementById('closeDrawerBtn');
    if (closeDrawerBtn) {
        closeDrawerBtn.addEventListener('click', hideNodeDetails);
    }
}

function showNodeDetails(nodeId) {
    const drawer = document.getElementById('nodeDetailsDrawer');
    const title = document.getElementById('drawerTitle');
    const content = document.getElementById('drawerContent');
    if (!drawer) return;

    drawer.classList.remove('hidden');
    title.textContent = nodeId;

    // Find all outgoing and incoming edges for this node
    const outgoing = (rawGraphData.edges || []).filter(e => e.from === nodeId);
    const incoming = (rawGraphData.edges || []).filter(e => e.to === nodeId);

    let html = `<div style="font-size: 0.85rem; display: flex; flex-direction: column; gap: 10px;">`;
    
    if (outgoing.length) {
        html += `<div><strong>Outgoing Relations (${outgoing.length}):</strong><ul style="padding-left: 16px; margin-top: 4px;">`;
        outgoing.forEach(e => {
            html += `<li>--[<em>${e.label}</em>]--> <strong>${e.to}</strong></li>`;
        });
        html += `</ul></div>`;
    }

    if (incoming.length) {
        html += `<div><strong>Incoming Relations (${incoming.length}):</strong><ul style="padding-left: 16px; margin-top: 4px;">`;
        incoming.forEach(e => {
            html += `<li><strong>${e.from}</strong> --[<em>${e.label}</em>]--></li>`;
        });
        html += `</ul></div>`;
    }

    if (!outgoing.length && !incoming.length) {
        html += `<p class="text-muted">Isolated entity node without active relational edges.</p>`;
    }

    html += `</div>`;
    content.innerHTML = html;
}

function hideNodeDetails() {
    const drawer = document.getElementById('nodeDetailsDrawer');
    if (drawer) drawer.classList.add('hidden');
}

// -----------------------------------------------------------------------------
// PURE CANVAS FORCE-DIRECTED GRAPH FALLBACK (100% OFFLINE CAPABLE)
// -----------------------------------------------------------------------------
function initCanvasGraphFallback(canvas, graphData) {
    const ctx = canvas.getContext('2d');
    const width = (canvas.width = canvas.parentElement.clientWidth || 800);
    const height = (canvas.height = canvas.parentElement.clientHeight || 550);

    const nodes = (graphData.nodes || []).map((n, i) => ({
        id: n.id,
        label: n.label,
        color: n.color || '#3b82f6',
        x: width / 2 + (Math.random() - 0.5) * 300,
        y: height / 2 + (Math.random() - 0.5) * 300,
        vx: 0,
        vy: 0
    }));

    const nodeIndex = {};
    nodes.forEach((n, idx) => nodeIndex[n.id] = idx);

    const edges = (graphData.edges || []).map(e => ({
        source: nodeIndex[e.from],
        target: nodeIndex[e.to],
        label: e.label
    })).filter(e => e.source !== undefined && e.target !== undefined);

    let animationFrame = null;

    function step() {
        // Spring physics
        edges.forEach(e => {
            const s = nodes[e.source];
            const t = nodes[e.target];
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = (dist - 90) * 0.02;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            s.vx += fx;
            s.vy += fy;
            t.vx -= fx;
            t.vy -= fy;
        });

        // Repulsion physics
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const a = nodes[i];
                const b = nodes[j];
                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const distSq = dx * dx + dy * dy || 1;
                if (distSq < 15000) {
                    const force = 300 / distSq;
                    a.vx -= dx * force;
                    a.vy -= dy * force;
                    b.vx += dx * force;
                    b.vy += dy * force;
                }
            }
        }

        // Center gravity and damping
        nodes.forEach(n => {
            n.vx += (width / 2 - n.x) * 0.002;
            n.vy += (height / 2 - n.y) * 0.002;
            n.vx *= 0.85;
            n.vy *= 0.85;
            n.x += n.vx;
            n.y += n.vy;
        });

        // Render
        ctx.clearRect(0, 0, width, height);

        // Draw edges
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = 1;
        edges.forEach(e => {
            const s = nodes[e.source];
            const t = nodes[e.target];
            ctx.beginPath();
            ctx.moveTo(s.x, s.y);
            ctx.lineTo(t.x, t.y);
            ctx.stroke();
        });

        // Draw nodes
        nodes.forEach(n => {
            ctx.beginPath();
            ctx.arc(n.x, n.y, 7, 0, Math.PI * 2);
            ctx.fillStyle = n.color;
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            ctx.fillStyle = '#cbd5e1';
            ctx.font = '10px Inter, sans-serif';
            ctx.fillText(n.label, n.x + 10, n.y + 3);
        });

        animationFrame = requestAnimationFrame(step);
    }

    step();
}
