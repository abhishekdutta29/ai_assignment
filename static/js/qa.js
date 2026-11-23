// KnowledgeLens - Q&A Dialogue & Reasoning Trace Interface

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const clearChatBtn = document.getElementById('clearChatBtn');

    // Profile drawer elements
    const toggleProfileBtn = document.getElementById('toggleProfileBtn');
    const profileDrawer = document.getElementById('studentProfileDrawer');
    const closeProfileBtn = document.getElementById('closeProfileBtn');
    const profileForm = document.getElementById('profileForm');
    const resetProfileBtn = document.getElementById('resetProfileBtn');

    // Trace elements
    const emptyTraceState = document.getElementById('emptyTraceState');
    const activeTraceContent = document.getElementById('activeTraceContent');
    const traceStatusBadge = document.getElementById('traceStatusBadge');
    const traceTechniqueName = document.getElementById('traceTechniqueName');
    const traceTechniqueRationale = document.getElementById('traceTechniqueRationale');
    const traceComplexity = document.getElementById('traceComplexity');
    const astQType = document.getElementById('astQType');
    const astPredicate = document.getElementById('astPredicate');
    const astEntitiesList = document.getElementById('astEntitiesList');
    const traceStepsList = document.getElementById('traceStepsList');
    const proofTreeSection = document.getElementById('proofTreeSection');
    const proofTreeContainer = document.getElementById('proofTreeContainer');
    const evidenceTriplesContainer = document.getElementById('evidenceTriplesContainer');

    // Student profile toggle
    if (toggleProfileBtn && profileDrawer) {
        toggleProfileBtn.addEventListener('click', () => {
            profileDrawer.classList.toggle('hidden');
        });
        if (closeProfileBtn) {
            closeProfileBtn.addEventListener('click', () => {
                profileDrawer.classList.add('hidden');
            });
        }
    }

    // Update Profile
    if (profileForm) {
        profileForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const coursesStr = document.getElementById('profCompletedCourses').value;
            const courses = coursesStr.split(',').map(s => s.trim().toUpperCase()).filter(s => s);

            const profileData = {
                student_id: document.getElementById('profStudentId').value.trim(),
                attendance: parseFloat(document.getElementById('profAttendance').value),
                cgpa: parseFloat(document.getElementById('profCgpa').value),
                completed_credits: parseInt(document.getElementById('profCredits').value),
                current_semester_credits: parseInt(document.getElementById('profSemesterCredits').value),
                completed_courses: courses
            };

            fetch('/api/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profileData)
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    window.showToast('Student Profile successfully updated!', 'success');
                    profileDrawer.classList.add('hidden');
                }
            });
        });
    }

    // Reset Profile
    if (resetProfileBtn) {
        resetProfileBtn.addEventListener('click', () => {
            document.getElementById('profStudentId').value = 'STD2026';
            document.getElementById('profAttendance').value = '80';
            document.getElementById('profCgpa').value = '3.8';
            document.getElementById('profCredits').value = '92';
            document.getElementById('profSemesterCredits').value = '16';
            document.getElementById('profCompletedCourses').value = 'CS101, MAT101, CS102, AI201, AI301, AI401';
            window.showToast('Reset form fields to default state.', 'info');
        });
    }

    // Example question chips
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const q = chip.dataset.q;
            if (q) {
                chatInput.value = q;
                submitQuestion(q);
            }
        });
    });

    // Clear chat
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            chatMessages.innerHTML = `
                <div class="message assistant-msg">
                    <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
                    <div class="msg-content">
                        <p>Dialogue history cleared. Ask a new question to resume symbolic reasoning.</p>
                    </div>
                </div>
            `;
            emptyTraceState.classList.remove('hidden');
            activeTraceContent.classList.add('hidden');
            traceStatusBadge.textContent = 'Awaiting Query';
            traceStatusBadge.className = 'badge badge-secondary';
        });
    }

    // Handle form submission
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const q = chatInput.value.trim();
            if (q) {
                submitQuestion(q);
            }
        });
    }

    function submitQuestion(questionText) {
        // Append user bubble
        appendMessage('user', questionText);
        chatInput.value = '';

        // Add loading bubble
        const loadingId = 'loading-' + Date.now();
        appendLoadingMessage(loadingId);

        traceStatusBadge.textContent = 'Reasoning in Progress...';
        traceStatusBadge.className = 'badge badge-warning';

        // Get current student profile from form fields if present
        let profilePayload = null;
        const attElem = document.getElementById('profAttendance');
        if (attElem) {
            const coursesStr = document.getElementById('profCompletedCourses').value;
            profilePayload = {
                student_id: document.getElementById('profStudentId').value.trim(),
                attendance: parseFloat(attElem.value),
                cgpa: parseFloat(document.getElementById('profCgpa').value),
                completed_credits: parseInt(document.getElementById('profCredits').value),
                current_semester_credits: parseInt(document.getElementById('profSemesterCredits').value),
                completed_courses: coursesStr.split(',').map(s => s.trim().toUpperCase()).filter(s => s)
            };
        }

        fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: questionText, profile: profilePayload })
        })
        .then(r => r.json())
        .then(data => {
            removeLoadingMessage(loadingId);
            if (data.status === 'success') {
                appendMessage('assistant', data.answer, data.evidence);
                renderTrace(data.trace, data.parsed_query, data.answer_status);
            } else {
                appendMessage('assistant', data.message || 'Error occurred during reasoning.');
            }
        })
        .catch(err => {
            removeLoadingMessage(loadingId);
            appendMessage('assistant', `Error connecting to inference engine: ${err}`);
        });
    }

    function appendMessage(sender, text, evidence = []) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-msg`;
        const icon = sender === 'user' ? 'fa-user' : 'fa-robot';

        let evidenceHtml = '';
        if (evidence && evidence.length > 0) {
            evidenceHtml = `<div style="margin-top: 8px; font-size: 0.78rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 6px; color: var(--text-secondary);">
                <strong>Supporting Evidence:</strong> ${evidence.map(e => `[Line ${e.source_line}: ${e.raw_text}]`).join(' ')}
            </div>`;
        }

        msgDiv.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid ${icon}"></i></div>
            <div class="msg-content">
                <p>${text}</p>
                ${evidenceHtml}
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendLoadingMessage(id) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant-msg';
        msgDiv.id = id;
        msgDiv.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid fa-spinner fa-spin"></i></div>
            <div class="msg-content">
                <p class="text-muted">Symbolic engine reasoning over Knowledge Base...</p>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeLoadingMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function renderTrace(trace, parsedQuery, answerStatus) {
        emptyTraceState.classList.add('hidden');
        activeTraceContent.classList.remove('hidden');

        traceStatusBadge.textContent = answerStatus === 'SUCCESS' ? 'Proof Verified' : 'Closed-World Boundary';
        traceStatusBadge.className = answerStatus === 'SUCCESS' ? 'badge badge-success' : 'badge badge-danger';

        traceTechniqueName.textContent = trace.technique_name;
        traceTechniqueRationale.textContent = trace.technique_rationale;
        traceComplexity.textContent = trace.time_complexity || 'O(1)';

        astQType.textContent = parsedQuery.qtype;
        astPredicate.textContent = parsedQuery.predicate || 'None';

        // Render entities
        astEntitiesList.innerHTML = '';
        if (parsedQuery.entity_resolutions && parsedQuery.entity_resolutions.length > 0) {
            parsedQuery.entity_resolutions.forEach(er => {
                const span = document.createElement('span');
                span.className = 'entity-pill';
                span.innerHTML = `<strong>${er.canonical}</strong> <small class="text-muted">(${er.method}, ${Math.round(er.confidence * 100)}%)</small>`;
                astEntitiesList.appendChild(span);
            });
        } else {
            astEntitiesList.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">None detected</span>';
        }

        // Render steps
        traceStepsList.innerHTML = '';
        (trace.steps || []).forEach(step => {
            const li = document.createElement('li');
            li.textContent = step;
            traceStepsList.appendChild(li);
        });

        // Render Proof Tree (if backward chaining)
        if (trace.proof_tree) {
            proofTreeSection.classList.remove('hidden');
            const pt = trace.proof_tree;
            let ptHtml = `<div style="margin-bottom: 6px;"><strong>Goal:</strong> <code>${pt.goal}</code> <span class="badge ${pt.status === 'PROVED' ? 'badge-success' : 'badge-danger'}">${pt.status}</span></div>`;
            ptHtml += `<div style="margin-bottom: 6px;"><strong>Rule:</strong> <em>${pt.rule_applied}</em></div>`;
            if (pt.subgoals && pt.subgoals.length) {
                ptHtml += `<div><strong>Subgoals:</strong><ul style="padding-left: 18px; margin-top: 4px;">`;
                pt.subgoals.forEach(sg => {
                    const badgeClass = sg.status === 'PROVED' ? 'badge-success' : 'badge-danger';
                    ptHtml += `<li><code>${sg.subgoal}</code> <span class="badge ${badgeClass}" style="font-size:0.65rem;">${sg.status}</span><br><small class="text-muted">${sg.fact}</small></li>`;
                });
                ptHtml += `</ul></div>`;
            }
            proofTreeContainer.innerHTML = ptHtml;
        } else {
            proofTreeSection.classList.add('hidden');
        }

        // Render Evidence Triples
        evidenceTriplesContainer.innerHTML = '';
        const triples = trace.supporting_triples || [];
        if (triples.length > 0) {
            triples.forEach(t => {
                const d = document.createElement('div');
                d.className = 'evidence-item';
                d.innerHTML = `
                    <div class="evidence-header">
                        <span>(${t.subject}, ${t.predicate}, ${t.object})</span>
                        <code style="font-size: 0.72rem;">${t.rule_id}</code>
                    </div>
                    <div class="evidence-sentence">Line ${t.source_line}: "${t.raw_text}"</div>
                `;
                evidenceTriplesContainer.appendChild(d);
            });
        } else {
            evidenceTriplesContainer.innerHTML = '<p class="text-muted" style="font-size: 0.82rem;">No supporting triples required (evaluated via boundary check or student state).</p>';
        }
    }
});
