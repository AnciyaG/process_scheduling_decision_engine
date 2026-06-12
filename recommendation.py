"""
Recommendation Module
Implements context-aware scheduling recommendation logic.
Features:
1. Classification Categories (Interactive, Batch, Critical)
2. Emergency Override for critical keywords (negation-aware)
3. Hybrid Scoring (70% Context Classification, 30% Simulation Metrics)
4. FCFS Selection capability for strongly sequential workloads with uniform burst times
5. Intelligent explanations comparing selected algorithms to the mathematical optimum
6. Stateless execution
"""

import re

# Classification categories
INTERACTIVE_KEYWORDS = ["chat", "messaging", "interactive", "response", "gaming", "realtime", "real-time", "short requests", "short request"]
BATCH_KEYWORDS = [
    "batch", "sequential", "payroll", "backup", "archiving", "rendering", "pipeline", 
    "predictable", "arrival order", "FIFO", "records processing", "document processing", 
    "routine processing", "batch jobs", "batch job"
]
CRITICAL_KEYWORDS = ["emergency", "critical", "hospital", "medical", "military", "urgent", "alert", "mission critical", "mission-critical", "safety"]

# Override keywords
OVERRIDE_KEYWORDS = ["emergency", "critical", "hospital", "medical", "urgent", "alert", "military", "mission critical"]

# Negation detection list
NEGATION_WORDS = {"no", "not", "none", "never", "without", "neither", "non", "lack", "lacking", "zero", "free", "avoid"}

def find_valid_matches(keywords: list, text: str) -> tuple:
    """
    Finds keyword matches in text, checking for negation in the preceding 3 words.
    Supports optional trailing 's' for simple plurals.
    
    Returns:
        tuple: (list of valid matches, list of negated matches)
    """
    valid = []
    negated = []
    text_lower = text.lower()
    
    for kw in keywords:
        # Match whole word/phrase with optional plural 's'
        pattern = rf'\b{re.escape(kw)}s?\b'
        for match in re.finditer(pattern, text_lower):
            match_start = match.start()
            preceding_text = text_lower[:match_start].strip()
            
            # Check last 3 tokens preceding the match
            tokens = re.findall(rf'\b\w+\b', preceding_text)
            last_tokens = tokens[-3:] if len(tokens) >= 3 else tokens
            
            if any(tok in NEGATION_WORDS for tok in last_tokens):
                negated.append(kw)
            else:
                valid.append(kw)
                
    return valid, negated

def generate_recommendations(analysis: dict, results: dict, workload_text: str = "") -> dict:
    """
    Selects Time-Optimized and Resource-Optimized recommendations using
    context classification, simulation results, and an emergency override filter.
    
    Args:
        analysis (dict): Semantic analysis results from analyzer.py
        results (dict): Averages and details from scheduler.py
        workload_text (str): The raw text description input by the user.
        
    Returns:
        dict: Time and Resource Optimized recommendations, along with debug output.
    """
    # 1. Normalise input
    text_to_analyze = workload_text if workload_text else analysis.get("workload_type", "")
    text_lower = text_to_analyze.lower()
    
    # Extract waiting times
    wt_fcfs = results["fcfs"]["averages"]["avg_waiting_time"]
    wt_sjf = results["sjf"]["averages"]["avg_waiting_time"]
    wt_prio = results["priority"]["averages"]["avg_waiting_time"]
    
    lowest_wt_val = min(wt_fcfs, wt_sjf, wt_prio)
    lowest_wt_algo = "FCFS" if lowest_wt_val == wt_fcfs else ("SJF" if lowest_wt_val == wt_sjf else "Priority Scheduling")

    # 2. EMERGENCY OVERRIDE CHECK
    valid_override_matches, negated_override_matches = find_valid_matches(OVERRIDE_KEYWORDS, text_lower)
    is_override = len(valid_override_matches) > 0
    
    if is_override:
        explanation = (
            "Priority Scheduling was selected because the workload contains emergency and critical keywords. "
            "In mission-critical environments, ensuring urgent processes execute first is more important "
            "than minimizing average waiting time."
        ) if lowest_wt_algo != "Priority Scheduling" else (
            "Priority Scheduling was selected because it achieved the lowest average waiting time and turnaround time "
            "while matching the workload's critical characteristics."
        )
        
        # Debugging Output
        print("\n[DEBUG] === EMERGENCY OVERRIDE TRIGGERED ===")
        print(f"[DEBUG] Matched Override Keywords: {valid_override_matches}")
        print(f"[DEBUG] Ignored Negated Overrides: {negated_override_matches}")
        print("[DEBUG] Final Recommendation forced to Priority Scheduling.\n")
        
        return {
            "time_optimized": "Priority Scheduling",
            "resource_optimized": "Priority Scheduling",
            "time_explanation": explanation,
            "resource_explanation": explanation,
            "detected_workload_type": analysis["workload_type"],
            "confidence_score": analysis["confidence"],
            "matched_fcfs_keywords": [],
            "matched_sjf_keywords": [],
            "matched_priority_keywords": valid_override_matches,
            "final_category_scores": {"fcfs": 0.0, "sjf": 0.0, "priority": 1.0}
        }

    # 3. HYBRID SCORING (For non-override workloads)
    # A. Context Match Scores
    valid_interactive, negated_int = find_valid_matches(INTERACTIVE_KEYWORDS, text_lower)
    valid_batch, negated_bat = find_valid_matches(BATCH_KEYWORDS, text_lower)
    valid_critical, negated_crit = find_valid_matches(CRITICAL_KEYWORDS, text_lower)
    
    all_negated = list(set(negated_int + negated_bat + negated_crit + negated_override_matches))
    
    raw_interactive = len(valid_interactive)
    raw_batch = len(valid_batch)
    raw_critical = len(valid_critical)
    
    max_raw = max(raw_interactive, raw_batch, raw_critical)
    if max_raw > 0:
        context_interactive = raw_interactive / max_raw
        context_batch = raw_batch / max_raw
        context_critical = raw_critical / max_raw
    else:
        context_interactive = 0.33
        context_batch = 0.33
        context_critical = 0.33

    # B. Simulation Performance Scores (Inverse Normalized Waiting Times)
    max_wt = max(wt_fcfs, wt_sjf, wt_prio)
    min_wt = min(wt_fcfs, wt_sjf, wt_prio)
    
    if max_wt > min_wt:
        sim_fcfs = 1.0 - (wt_fcfs - min_wt) / (max_wt - min_wt)
        sim_sjf = 1.0 - (wt_sjf - min_wt) / (max_wt - min_wt)
        sim_prio = 1.0 - (wt_prio - min_wt) / (max_wt - min_wt)
    else:
        sim_fcfs = 1.0
        sim_sjf = 1.0
        sim_prio = 1.0
        
    # C. Calculate Final Scores (70% Context, 30% Simulation Performance)
    score_interactive = (context_interactive * 0.7) + (sim_sjf * 0.3)
    score_batch = (context_batch * 0.7) + (sim_fcfs * 0.3)
    score_critical = (context_critical * 0.7) + (sim_prio * 0.3)
    
    # 4. SELECT CATEGORY WINNER
    score_map = [
        ('CRITICAL', score_critical),
        ('INTERACTIVE', score_interactive),
        ('BATCH', score_batch)
    ]
    winning_category = max(score_map, key=lambda x: x[1])[0]
    
    # Debugging Output
    print("\n[DEBUG] === HYBRID RECOMMENDATION DECISION ===")
    print(f"[DEBUG] Matched FCFS keywords: {list(set(valid_batch))}")
    print(f"[DEBUG] Matched SJF keywords: {list(set(valid_interactive))}")
    print(f"[DEBUG] Matched Priority keywords: {list(set(valid_critical))}")
    print(f"[DEBUG] Negated matches ignored: {all_negated}")
    print(f"[DEBUG] Final Scores: BATCH={score_batch:.2f}, INTERACTIVE={score_interactive:.2f}, CRITICAL={score_critical:.2f}")
    print(f"[DEBUG] Selected Domain Category: {winning_category}\n")
    
    # 5. RESOLVE RECOMMENDATIONS & EXPLANATIONS
    if winning_category == 'CRITICAL':
        time_optimized = "Priority Scheduling"
        resource_optimized = "Priority Scheduling"
        
        time_explanation = (
            "Although SJF achieved a lower average waiting time, Priority Scheduling was selected because the workload contains critical and emergency tasks. "
            "In mission-critical environments, ensuring urgent processes execute first is more important than minimizing average waiting time."
        ) if lowest_wt_algo != "Priority Scheduling" else (
            "Priority Scheduling was selected because it achieved the lowest average waiting time and turnaround time while matching the workload's critical characteristics."
        )
        resource_explanation = time_explanation

    elif winning_category == 'INTERACTIVE':
        time_optimized = "SJF"
        resource_optimized = "FCFS"
        
        time_explanation = (
            "SJF was selected because it achieved the lowest average waiting time and turnaround time while matching the workload's interactive characteristics."
        )
        resource_explanation = (
            "FCFS was selected because the workload is highly sequential and predictable. FCFS preserves arrival order, ensures fairness, and introduces minimal scheduling overhead."
        )
        
    else: # BATCH
        # Check standard deviation of burst times to see if they are uniform / similar
        similar_burst_times = False
        procs = results.get("fcfs", {}).get("processes", [])
        if procs:
            bt_list = [p["burst_time"] for p in procs]
            mean_bt = sum(bt_list) / len(bt_list)
            var_bt = sum((x - mean_bt) ** 2 for x in bt_list) / len(bt_list)
            std_dev = var_bt ** 0.5
            max_ratio = max(bt_list) / max(min(bt_list), 1)
            similar_burst_times = (std_dev <= 3.0) or (max_ratio <= 1.5)
            
        # If strongly BATCH and similar burst times, allow FCFS to be selected as Time Optimized
        is_strongly_batch = (raw_batch >= 2 or score_batch >= 0.6)
        
        if is_strongly_batch and similar_burst_times:
            time_optimized = "FCFS"
            resource_optimized = "FCFS"
            
            time_explanation = (
                "Although SJF achieved a lower average waiting time, FCFS was selected because the workload is highly sequential and predictable. "
                "FCFS preserves arrival order, ensures fairness, and introduces minimal scheduling overhead."
            ) if lowest_wt_algo != "FCFS" else (
                "FCFS was selected because it matched the workload's sequential characteristics and achieved the lowest average waiting time."
            )
            resource_explanation = (
                "FCFS was selected because the workload is highly sequential and predictable. FCFS preserves arrival order, ensures fairness, and introduces minimal scheduling overhead."
            )
        else:
            time_optimized = "SJF"
            resource_optimized = "FCFS"
            
            time_explanation = (
                "SJF was selected because it achieved the lowest average waiting time and turnaround time while matching the workload's interactive characteristics."
            )
            resource_explanation = (
                "FCFS was selected because the workload is highly sequential and predictable. FCFS preserves arrival order, ensures fairness, and introduces minimal scheduling overhead."
            )
            
    return {
        "time_optimized": time_optimized,
        "resource_optimized": resource_optimized,
        "time_explanation": time_explanation,
        "resource_explanation": resource_explanation,
        "detected_workload_type": analysis["workload_type"],
        "confidence_score": analysis["confidence"],
        "matched_fcfs_keywords": list(set(valid_batch)),
        "matched_sjf_keywords": list(set(valid_interactive)),
        "matched_priority_keywords": list(set(valid_critical)),
        "final_category_scores": {
            "fcfs": round(score_batch, 2),
            "sjf": round(score_interactive, 2),
            "priority": round(score_critical, 2)
        }
    }
