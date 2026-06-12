"""
Workload Analyzer Module
Analyzes natural language workload descriptions using keyword matching and weights,
determining the workload type, confidence, and system characteristics.
Implements stateless negation-aware matching to ignore negated terms.
"""

import re

# Keyword definitions with associated weights
KEYWORD_MAPPINGS = {
    'fcfs': {
        'sequential': 2.0,
        'batch': 2.0,
        'predictable': 1.5,
        'logging': 1.5,
        'pipeline': 1.5,
        'rendering': 2.0,
        'overnight': 1.5,
        'offline': 1.5,
        'backup': 1.5,
        'bulk': 1.0
    },
    'sjf': {
        'interactive': 2.0,
        'realtime': 2.0,
        'real-time': 2.0,
        'fast': 1.5,
        'chat': 2.0,
        'short requests': 2.5,
        'responsiveness': 2.0,
        'response': 1.5,
        'ui': 1.5,
        'query': 1.5,
        'quick': 1.0
    },
    'priority': {
        'emergency': 2.5,
        'critical': 2.5,
        'medical': 2.0,
        'military': 2.0,
        'urgent': 2.0,
        'mission critical': 2.5,
        'mission-critical': 2.5,
        'hospital': 1.5,
        'alert': 2.0,
        'vip': 1.5,
        'safety': 2.0,
        'high priority': 2.0
    }
}

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

def analyze_workload(text: str) -> dict:
    """
    Analyzes natural language workload descriptions in a completely stateless manner.
    
    Args:
        text (str): The workload description entered by the user.
        
    Returns:
        dict: Analysis results containing categories, scores, confidence, flags, and debug info.
    """
    if not text or not isinstance(text, str):
        return {
            "workload_type": "Batch Processing (FCFS)",
            "category": "fcfs",
            "confidence": 0.50,
            "scores": {"fcfs": 0.0, "sjf": 0.0, "priority": 0.0},
            "attributes": {
                "is_realtime": False,
                "is_batch": True,
                "is_short": False,
                "is_long": False,
                "is_critical": False,
                "is_priority_sensitive": False
            },
            "debug_info": {
                "matched_fcfs_keywords": [],
                "matched_sjf_keywords": [],
                "matched_priority_keywords": [],
                "negated_matches_ignored": []
            }
        }
        
    text_lower = text.lower()
    
    # Scores and matches tracking
    scores = {"fcfs": 0.0, "sjf": 0.0, "priority": 0.0}
    debug_matches = {"fcfs": [], "sjf": [], "priority": []}
    all_negated = []
    
    for category, keywords_dict in KEYWORD_MAPPINGS.items():
        valid_list, negated_list = find_valid_matches(list(keywords_dict.keys()), text_lower)
        all_negated.extend(negated_list)
        
        for kw in valid_list:
            weight = keywords_dict[kw]
            scores[category] += weight
            debug_matches[category].append(kw)
            
    # Calculate attributes based on valid matches
    is_realtime = len(debug_matches["sjf"]) > 0
    is_batch = len(debug_matches["fcfs"]) > 0 or (len(debug_matches["sjf"]) == 0 and len(debug_matches["priority"]) == 0)
    is_short = is_realtime
    is_long = is_batch
    is_critical = len(debug_matches["priority"]) > 0
    is_priority_sensitive = is_critical
    
    # Determine winning category
    total_score = sum(scores.values())
    if total_score > 0:
        winning_category = max(scores, key=scores.get)
        confidence = round(scores[winning_category] / total_score, 2)
    else:
        winning_category = "fcfs"
        confidence = 0.33
        
    category_names = {
        "fcfs": "Batch Processing (FCFS)",
        "sjf": "Real-Time / Short Jobs (SJF)",
        "priority": "Emergency / Critical (Priority Scheduling)"
    }
    
    return {
        "workload_type": category_names[winning_category],
        "category": winning_category,
        "confidence": confidence,
        "scores": {k: round(v, 2) for k, v in scores.items()},
        "attributes": {
            "is_realtime": is_realtime,
            "is_batch": is_batch,
            "is_short": is_short,
            "is_long": is_long,
            "is_critical": is_critical,
            "is_priority_sensitive": is_priority_sensitive
        },
        "debug_info": {
            "matched_fcfs_keywords": list(set(debug_matches["fcfs"])),
            "matched_sjf_keywords": list(set(debug_matches["sjf"])),
            "matched_priority_keywords": list(set(debug_matches["priority"])),
            "negated_matches_ignored": list(set(all_negated))
        }
    }
