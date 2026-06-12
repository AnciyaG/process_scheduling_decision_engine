"""
Scheduler Module
Generates workload-aware processes and simulates scheduling algorithms:
- First Come First Serve (FCFS)
- Shortest Job First (SJF) [Non-Preemptive]
- Priority Scheduling [Non-Preemptive]
Calculates Completion Time (CT), Turnaround Time (TAT), Waiting Time (WT),
and Response Time (RT) for each algorithm and generates Gantt chart data.
"""

import hashlib
import random

def get_stable_seed(text: str) -> int:
    """Generates a stable integer seed from a string description."""
    h = hashlib.md5(text.encode('utf-8')).hexdigest()
    return int(h, 16) % 1000000

def generate_processes(attributes: dict, workload_text: str) -> list:
    """
    Generates between 5 and 15 synthetic processes based on workload attributes.
    Uses md5 hash of the workload description to ensure deterministic generation.
    """
    seed = get_stable_seed(workload_text)
    rng = random.Random(seed)
    
    num_processes = rng.randint(6, 12)
    processes = []
    
    # Workload-specific ranges
    is_realtime = attributes.get("is_realtime", False)
    is_batch = attributes.get("is_batch", False)
    is_critical = attributes.get("is_critical", False)
    is_short = attributes.get("is_short", False)
    is_long = attributes.get("is_long", False)
    is_priority = attributes.get("is_priority_sensitive", False)
    
    for i in range(num_processes):
        pid = f"P{i+1}"
        
        # Ensure at least one process arrives at 0
        if i == 0:
            arrival_time = 0
        else:
            arrival_time = rng.randint(0, 12)
            
        # Determine Burst Time based on workload characteristics
        if is_realtime or is_short:
            burst_time = rng.randint(1, 5)
        elif is_batch or is_long:
            burst_time = rng.randint(15, 40)
        else:
            burst_time = rng.randint(3, 12)
            
        # Determine Priority based on critical/emergency characteristics
        # Priority 1 = Highest, 10 = Lowest
        if is_critical or is_priority:
            # Generate higher priority for critical tasks
            if rng.random() < 0.5:
                priority = rng.randint(1, 4)  # Urgent
            else:
                priority = rng.randint(5, 10) # Standard/Low
        else:
            priority = rng.randint(1, 10)
            
        processes.append({
            "pid": pid,
            "arrival_time": arrival_time,
            "burst_time": burst_time,
            "priority": priority
        })
        
    # Sort processes by Arrival Time initially for nice presentation
    processes.sort(key=lambda x: (x["arrival_time"], int(x["pid"][1:])))
    return processes

def calculate_averages(completed_processes: list) -> dict:
    """Calculates average WT, TAT, and RT."""
    n = len(completed_processes)
    if n == 0:
        return {"avg_waiting_time": 0, "avg_turnaround_time": 0, "avg_response_time": 0}
        
    total_wt = sum(p["waiting_time"] for p in completed_processes)
    total_tat = sum(p["turnaround_time"] for p in completed_processes)
    total_rt = sum(p["response_time"] for p in completed_processes)
    
    return {
        "avg_waiting_time": round(total_wt / n, 2),
        "avg_turnaround_time": round(total_tat / n, 2),
        "avg_response_time": round(total_rt / n, 2)
    }

def simulate_fcfs(processes: list) -> dict:
    """
    Simulates First-Come-First-Serve (FCFS) Scheduling.
    Sorts by arrival_time. Ties broken by PID.
    """
    # Create a copy to avoid mutating source
    local_procs = [dict(p) for p in processes]
    # Sort by arrival time, then by process number/ID
    local_procs.sort(key=lambda x: (x["arrival_time"], int(x["pid"][1:])))
    
    completed = []
    gantt = []
    current_time = 0
    
    for p in local_procs:
        if current_time < p["arrival_time"]:
            gantt.append({
                "pid": "IDLE",
                "start": current_time,
                "end": p["arrival_time"]
            })
            current_time = p["arrival_time"]
            
        start_time = current_time
        completion_time = start_time + p["burst_time"]
        turnaround_time = completion_time - p["arrival_time"]
        waiting_time = turnaround_time - p["burst_time"]
        response_time = start_time - p["arrival_time"]
        
        p.update({
            "start_time": start_time,
            "completion_time": completion_time,
            "turnaround_time": turnaround_time,
            "waiting_time": waiting_time,
            "response_time": response_time
        })
        
        gantt.append({
            "pid": p["pid"],
            "start": start_time,
            "end": completion_time
        })
        current_time = completion_time
        completed.append(p)
        
    # Sort back by PID for consistent tabular display
    completed.sort(key=lambda x: int(x["pid"][1:]))
    
    return {
        "processes": completed,
        "averages": calculate_averages(completed),
        "gantt": gantt
    }

def simulate_sjf(processes: list) -> dict:
    """
    Simulates Non-Preemptive Shortest Job First (SJF) Scheduling.
    At any decision point, schedules the arrived job with shortest burst time.
    Ties broken by arrival time, then by PID.
    """
    remaining = [dict(p) for p in processes]
    completed = []
    gantt = []
    current_time = 0
    
    while remaining:
        # Filter processes that have arrived by current_time
        ready = [p for p in remaining if p["arrival_time"] <= current_time]
        
        if not ready:
            # CPU is idle; find the next process that will arrive
            next_arrival = min(p["arrival_time"] for p in remaining)
            gantt.append({
                "pid": "IDLE",
                "start": current_time,
                "end": next_arrival
            })
            current_time = next_arrival
            continue
            
        # Pick process with shortest burst time
        # Tie-break: arrival time, then PID number
        selected = min(ready, key=lambda x: (x["burst_time"], x["arrival_time"], int(x["pid"][1:])))
        
        start_time = current_time
        completion_time = start_time + selected["burst_time"]
        turnaround_time = completion_time - selected["arrival_time"]
        waiting_time = turnaround_time - selected["burst_time"]
        response_time = start_time - selected["arrival_time"]
        
        selected.update({
            "start_time": start_time,
            "completion_time": completion_time,
            "turnaround_time": turnaround_time,
            "waiting_time": waiting_time,
            "response_time": response_time
        })
        
        gantt.append({
            "pid": selected["pid"],
            "start": start_time,
            "end": completion_time
        })
        
        current_time = completion_time
        remaining.remove(selected)
        completed.append(selected)
        
    completed.sort(key=lambda x: int(x["pid"][1:]))
    return {
        "processes": completed,
        "averages": calculate_averages(completed),
        "gantt": gantt
    }

def simulate_priority(processes: list) -> dict:
    """
    Simulates Non-Preemptive Priority Scheduling.
    At any decision point, schedules the arrived job with highest priority (lowest priority value).
    Ties broken by arrival time, then by PID.
    """
    remaining = [dict(p) for p in processes]
    completed = []
    gantt = []
    current_time = 0
    
    while remaining:
        # Filter processes that have arrived by current_time
        ready = [p for p in remaining if p["arrival_time"] <= current_time]
        
        if not ready:
            # CPU is idle; find the next process that will arrive
            next_arrival = min(p["arrival_time"] for p in remaining)
            gantt.append({
                "pid": "IDLE",
                "start": current_time,
                "end": next_arrival
            })
            current_time = next_arrival
            continue
            
        # Pick process with highest priority (lowest numerical value, e.g. 1 is highest)
        # Tie-break: arrival time, then PID number
        selected = min(ready, key=lambda x: (x["priority"], x["arrival_time"], int(x["pid"][1:])))
        
        start_time = current_time
        completion_time = start_time + selected["burst_time"]
        turnaround_time = completion_time - selected["arrival_time"]
        waiting_time = turnaround_time - selected["burst_time"]
        response_time = start_time - selected["arrival_time"]
        
        selected.update({
            "start_time": start_time,
            "completion_time": completion_time,
            "turnaround_time": turnaround_time,
            "waiting_time": waiting_time,
            "response_time": response_time
        })
        
        gantt.append({
            "pid": selected["pid"],
            "start": start_time,
            "end": completion_time
        })
        
        current_time = completion_time
        remaining.remove(selected)
        completed.append(selected)
        
    completed.sort(key=lambda x: int(x["pid"][1:]))
    return {
        "processes": completed,
        "averages": calculate_averages(completed),
        "gantt": gantt
    }
