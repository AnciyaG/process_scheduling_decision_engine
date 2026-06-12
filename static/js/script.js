/**
 * Process Scheduling Decision Engine - Client Side Logic
 * Handles interactive tabs, quick example fills, form submission, 
 * rendering dynamic tables, building HTML Gantt charts, and Chart.js integration.
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const workloadForm = document.getElementById('workload-form');
    const workloadInput = document.getElementById('workload-input');
    const exampleBtns = document.querySelectorAll('.btn-example');
    const btnSubmit = document.getElementById('btn-submit');
    const loader = document.getElementById('loader');
    const resultsPanel = document.getElementById('results-panel');
    
    // Diagnostic elements
    const detectedTypeBadge = document.getElementById('detected-type-badge');
    const confidenceVal = document.getElementById('confidence-val');
    
    // Recommendations
    const timeOptAlgo = document.getElementById('time-opt-algo');
    const timeOptMetric = document.getElementById('time-opt-metric');
    const timeOptDesc = document.getElementById('time-opt-desc');
    const resOptAlgo = document.getElementById('res-opt-algo');
    const resOptDesc = document.getElementById('res-opt-desc');
    
    // Tables
    const processesTableBody = document.querySelector('#processes-table tbody');
    const fcfsTableBody = document.querySelector('#fcfs-table tbody');
    const sjfTableBody = document.querySelector('#sjf-table tbody');
    const priorityTableBody = document.querySelector('#priority-table tbody');
    
    // Averages elements
    const fcfsAvgWt = document.getElementById('fcfs-avg-wt');
    const fcfsAvgTat = document.getElementById('fcfs-avg-tat');
    const fcfsAvgRt = document.getElementById('fcfs-avg-rt');
    
    const sjfAvgWt = document.getElementById('sjf-avg-wt');
    const sjfAvgTat = document.getElementById('sjf-avg-tat');
    const sjfAvgRt = document.getElementById('sjf-avg-rt');
    
    const priorityAvgWt = document.getElementById('priority-avg-wt');
    const priorityAvgTat = document.getElementById('priority-avg-tat');
    const priorityAvgRt = document.getElementById('priority-avg-rt');
    
    // Gantt Containers
    const ganttFcfs = document.getElementById('gantt-fcfs');
    const scaleFcfs = document.getElementById('scale-fcfs');
    const ganttSjf = document.getElementById('gantt-sjf');
    const scaleSjf = document.getElementById('scale-sjf');
    const ganttPriority = document.getElementById('gantt-priority');
    const scalePriority = document.getElementById('scale-priority');

    // Chart Instance Holder
    let comparisonChartInstance = null;

    /* ==========================================================================
       1. Tab Switching Functionality
       ========================================================================== */
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and panes
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            // Add active class to current button and corresponding pane
            btn.classList.add('active');
            const targetPaneId = btn.getAttribute('data-tab');
            document.getElementById(targetPaneId).classList.add('active');
        });
    });

    /* ==========================================================================
       2. Quick Examples Click Handlers
       ========================================================================== */
    exampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const exampleText = btn.getAttribute('data-text');
            workloadInput.value = exampleText;
            workloadInput.focus();
            
            // Auto-submit form
            workloadForm.dispatchEvent(new Event('submit'));
        });
    });

    /* ==========================================================================
       3. Form Submission & Fetch API
       ========================================================================== */
    workloadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const textValue = workloadInput.value.trim();
        if (!textValue) return;

        // Visual feedback - Show loader and disable submit button
        loader.classList.remove('hidden');
        btnSubmit.disabled = true;
        resultsPanel.classList.add('hidden');

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ workload: textValue })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Network error occurred');
            }

            const data = await response.json();
            
            // Process and display the data
            renderDashboard(data);
            
            // Show results section
            resultsPanel.classList.remove('hidden');
            
            // Smooth scroll to results
            resultsPanel.scrollIntoView({ behavior: 'smooth' });

        } catch (err) {
            console.error('Submission Error:', err);
            alert(`Error: ${err.message || 'An error occurred during calculation'}`);
        } finally {
            // Hide loader and enable submit button
            loader.classList.add('hidden');
            btnSubmit.disabled = false;
        }
    });

    /* ==========================================================================
       4. Render Dashboard Core Elements
       ========================================================================== */
    function renderDashboard(data) {
        // Set badges
        detectedTypeBadge.textContent = data.detected_workload_type;
        confidenceVal.textContent = `${Math.round(data.confidence_score * 100)}%`;

        // Render Recommendations
        const timeAlgo = data.recommendations.time_optimized;
        const timeKey = timeAlgo.toLowerCase().includes('fcfs') ? 'fcfs' : 
                        (timeAlgo.toLowerCase().includes('sjf') ? 'sjf' : 'priority');
        const timeWt = data.results[timeKey].averages.avg_waiting_time;

        timeOptAlgo.textContent = timeAlgo;
        timeOptMetric.innerHTML = `Avg Waiting: <span class="neon-text-blue">${timeWt}s</span>`;
        timeOptDesc.textContent = data.recommendations.time_explanation;

        resOptAlgo.textContent = data.recommendations.resource_optimized;
        resOptDesc.textContent = data.recommendations.resource_explanation;

        // Populate tables
        populateProcessesTable(data.generated_processes);
        
        populateSimulationTable(fcfsTableBody, data.results.fcfs.processes);
        fcfsAvgWt.textContent = `${data.results.fcfs.averages.avg_waiting_time}s`;
        fcfsAvgTat.textContent = `${data.results.fcfs.averages.avg_turnaround_time}s`;
        fcfsAvgRt.textContent = `${data.results.fcfs.averages.avg_response_time}s`;

        populateSimulationTable(sjfTableBody, data.results.sjf.processes);
        sjfAvgWt.textContent = `${data.results.sjf.averages.avg_waiting_time}s`;
        sjfAvgTat.textContent = `${data.results.sjf.averages.avg_turnaround_time}s`;
        sjfAvgRt.textContent = `${data.results.sjf.averages.avg_response_time}s`;

        populateSimulationTable(priorityTableBody, data.results.priority.processes);
        priorityAvgWt.textContent = `${data.results.priority.averages.avg_waiting_time}s`;
        priorityAvgTat.textContent = `${data.results.priority.averages.avg_turnaround_time}s`;
        priorityAvgRt.textContent = `${data.results.priority.averages.avg_response_time}s`;

        // Render Gantt charts
        renderGanttChart(ganttFcfs, scaleFcfs, data.results.fcfs.gantt);
        renderGanttChart(ganttSjf, scaleSjf, data.results.sjf.gantt);
        renderGanttChart(ganttPriority, scalePriority, data.results.priority.gantt);

        // Render Charts comparison
        buildComparisonChart(data.results);
    }

    /* ==========================================================================
       5. Populate Tables Helper Functions
       ========================================================================== */
    function populateProcessesTable(processes) {
        processesTableBody.innerHTML = '';
        processes.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${p.pid}</strong></td>
                <td>${p.arrival_time}s</td>
                <td>${p.burst_time}s</td>
                <td><span class="priority-indicator priority-${Math.ceil(p.priority/2)}">${p.priority}</span></td>
            `;
            processesTableBody.appendChild(tr);
        });
    }

    function populateSimulationTable(tbody, processes) {
        tbody.innerHTML = '';
        processes.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${p.pid}</strong></td>
                <td>${p.arrival_time}s</td>
                <td>${p.burst_time}s</td>
                <td>${p.priority}</td>
                <td>${p.start_time}s</td>
                <td>${p.completion_time}s</td>
                <td class="neon-text-purple">${p.turnaround_time}s</td>
                <td class="neon-text-blue">${p.waiting_time}s</td>
                <td>${p.response_time}s</td>
            `;
            tbody.appendChild(tr);
        });
    }

    /* ==========================================================================
       6. Dynamic Gantt Chart Builder
       ========================================================================== */
    function renderGanttChart(ganttContainer, scaleContainer, ganttData) {
        ganttContainer.innerHTML = '';
        scaleContainer.innerHTML = '';

        if (!ganttData || ganttData.length === 0) return;

        const totalDuration = ganttData[ganttData.length - 1].end;

        // Render gantt blocks
        ganttData.forEach(block => {
            const blockDuration = block.end - block.start;
            const pctWidth = (blockDuration / totalDuration) * 100;

            const div = document.createElement('div');
            div.className = `gantt-block`;
            
            // Assign gradient color class
            if (block.pid === 'IDLE') {
                div.classList.add('gantt-idle');
                div.textContent = 'IDLE';
            } else {
                const pNum = parseInt(block.pid.replace('P', ''), 10);
                // Cycle colors if process number exceeds 12
                const colorIndex = ((pNum - 1) % 12) + 1;
                div.classList.add(`gantt-p${colorIndex}`);
                div.textContent = block.pid;
            }

            div.style.width = `${pctWidth}%`;

            // Tooltip creation
            const tooltip = document.createElement('span');
            tooltip.className = 'tooltip';
            if (block.pid === 'IDLE') {
                tooltip.innerHTML = `CPU Idle<br>Duration: ${blockDuration}s<br>Time: ${block.start}s → ${block.end}s`;
            } else {
                tooltip.innerHTML = `<strong>Process ${block.pid}</strong><br>Start: ${block.start}s<br>End: ${block.end}s<br>Duration: ${blockDuration}s`;
            }
            div.appendChild(tooltip);
            ganttContainer.appendChild(div);
        });

        // Render scale ticks
        // Draw tick intervals depending on total duration
        let interval = 5;
        if (totalDuration > 100) {
            interval = 20;
        } else if (totalDuration > 50) {
            interval = 10;
        } else if (totalDuration <= 15) {
            interval = 2;
        }

        // Draw ticks at regular intervals
        for (let i = 0; i <= totalDuration; i += interval) {
            drawTick(scaleContainer, i, totalDuration);
        }
        
        // Ensure final completion tick is always drawn
        if (totalDuration % interval !== 0) {
            drawTick(scaleContainer, totalDuration, totalDuration);
        }
    }

    function drawTick(container, val, total) {
        const pctLeft = (val / total) * 100;
        const tickSpan = document.createElement('span');
        tickSpan.className = 'scale-tick';
        tickSpan.style.left = `${pctLeft}%`;
        tickSpan.innerHTML = `${val}s`;
        container.appendChild(tickSpan);
    }

    /* ==========================================================================
       7. Chart.js Performance Bar Chart Builder
       ========================================================================== */
    function buildComparisonChart(results) {
        const ctx = document.getElementById('comparison-chart').getContext('2d');

        // Destroy existing chart instance to prevent overlaps on redraw
        if (comparisonChartInstance) {
            comparisonChartInstance.destroy();
        }

        // Extract averages for the three algorithms
        const labels = ['FCFS', 'SJF', 'Priority'];
        
        const dataWaiting = [
            results.fcfs.averages.avg_waiting_time,
            results.sjf.averages.avg_waiting_time,
            results.priority.averages.avg_waiting_time
        ];

        const dataTurnaround = [
            results.fcfs.averages.avg_turnaround_time,
            results.sjf.averages.avg_turnaround_time,
            results.priority.averages.avg_turnaround_time
        ];

        const dataResponse = [
            results.fcfs.averages.avg_response_time,
            results.sjf.averages.avg_response_time,
            results.priority.averages.avg_response_time
        ];

        comparisonChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Avg Waiting Time (s)',
                        data: dataWaiting,
                        backgroundColor: 'rgba(0, 242, 254, 0.65)',
                        borderColor: '#00f2fe',
                        borderWidth: 1.5,
                        borderRadius: 6,
                    },
                    {
                        label: 'Avg Turnaround Time (s)',
                        data: dataTurnaround,
                        backgroundColor: 'rgba(189, 0, 255, 0.65)',
                        borderColor: '#bd00ff',
                        borderWidth: 1.5,
                        borderRadius: 6,
                    },
                    {
                        label: 'Avg Response Time (s)',
                        data: dataResponse,
                        backgroundColor: 'rgba(255, 0, 127, 0.65)',
                        borderColor: '#ff007f',
                        borderWidth: 1.5,
                        borderRadius: 6,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                        },
                        ticks: {
                            color: '#a0aec0',
                            font: {
                                family: 'Outfit',
                                size: 12
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                        },
                        ticks: {
                            color: '#a0aec0',
                            font: {
                                family: 'Inter',
                                size: 11
                            }
                        },
                        title: {
                            display: true,
                            text: 'Duration (Seconds)',
                            color: '#718096',
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#f8f9fa',
                            font: {
                                family: 'Inter',
                                size: 11
                            },
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0f0c1e',
                        titleFont: {
                            family: 'Outfit',
                            size: 13,
                        },
                        bodyFont: {
                            family: 'Inter',
                            size: 12,
                        },
                        borderColor: 'rgba(255,255,255,0.15)',
                        borderWidth: 1,
                        padding: 10,
                        displayColors: true
                    }
                }
            }
        });
    }
});
