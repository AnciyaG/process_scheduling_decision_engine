"""
Flask Application Entry Point
Sets up the web server routes and the POST /api/analyze endpoint to orchestrate
workload analysis, simulation execution, and recommendation generation.
"""

from flask import Flask, render_template, request, jsonify
from analyzer import analyze_workload
from scheduler import generate_processes, simulate_fcfs, simulate_sjf, simulate_priority
from recommendation import generate_recommendations

app = Flask(__name__)

@app.route('/')
def index():
    """Renders the dashboard landing page."""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    Analyzes user text, generates matching workload processes,
    simulates FCFS, SJF, and Priority Scheduling algorithms,
    and returns recommendations and Gantt/Chart data.
    """
    try:
        data = request.get_json()
        if not data or 'workload' not in data:
            return jsonify({"error": "Invalid request. JSON body must contain a 'workload' field."}), 400
        
        workload_text = data['workload'].strip()
        if not workload_text:
            return jsonify({"error": "Workload description cannot be empty."}), 400
            
        # 1. Analyze workload semantics
        analysis = analyze_workload(workload_text)
        
        # 2. Generate workload-aware processes
        processes = generate_processes(analysis['attributes'], workload_text)
        
        # 3. Simulate algorithms
        fcfs_results = simulate_fcfs(processes)
        sjf_results = simulate_sjf(processes)
        priority_results = simulate_priority(processes)
        
        # Combine simulation results
        simulation_results = {
            "fcfs": fcfs_results,
            "sjf": sjf_results,
            "priority": priority_results
        }
        
        # 4. Generate recommendations
        recommendations = generate_recommendations(analysis, simulation_results, workload_text)
        
        # Return response matching API specifications
        response_payload = {
            "detected_workload_type": analysis["workload_type"],
            "confidence_score": analysis["confidence"],
            "generated_processes": processes,
            "results": simulation_results,
            "recommendations": recommendations
        }
        
        return jsonify(response_payload)
        
    except Exception as e:
        app.logger.error(f"Error during workload analysis: {str(e)}")
        return jsonify({"error": "An internal server error occurred while processing the workload."}), 500

if __name__ == '__main__':
    # Run Flask application on port 5000 in debug mode
    app.run(host='127.0.0.1', port=5000, debug=True)
