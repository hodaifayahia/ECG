"""
Machine Learning Feature Selector
Extract only the most important features for ML models from full ECG metrics
"""

import json


# Define important features for different ML use cases
FEATURE_SETS = {
    # Basic: Top 5 most reliable ECG features
    'basic': [
        'heart_rate_bpm',
        'sdnn_ms',
        'rmssd_ms',
        'lf_hf_ratio',
        'pnn50_percent'
    ],
    
    # Standard: 7 features (recommended for most models)
    'standard': [
        'heart_rate_bpm',
        'sdnn_ms',
        'rmssd_ms',
        'pnn50_percent',
        'pnn20_percent',
        'sd1_ms',
        'lf_hf_ratio'
    ],
    
    # Complete: All 10 metrics
    'complete': [
        'heart_rate_bpm',
        'sdnn_ms',
        'rmssd_ms',
        'pnn50_percent',
        'pnn20_percent',
        'sd1_ms',
        'sd2_ms',
        'lf_power',
        'hf_power',
        'lf_hf_ratio'
    ]
}


def select_features(metrics, feature_set='standard'):
    """
    Extract only important features from full metrics
    
    Args:
        metrics: dict - Full metrics from analyse.compute_metrics()
        feature_set: str - 'basic', 'standard', or 'complete'
    
    Returns:
        dict - Only the selected features
        
    Example:
        >>> full_metrics = {'heart_rate_bpm': 70, 'sdnn_ms': 50, ...}
        >>> ml_features = select_features(full_metrics, 'standard')
        >>> # Returns only 7 important features
    """
    
    if feature_set not in FEATURE_SETS:
        raise ValueError(f"Unknown feature_set: {feature_set}. Use: {list(FEATURE_SETS.keys())}")
    
    selected = {}
    features_to_use = FEATURE_SETS[feature_set]
    
    for feature in features_to_use:
        if feature in metrics:
            selected[feature] = metrics[feature]
        else:
            print(f"⚠ Warning: Feature '{feature}' not found in metrics")
    
    return selected


def get_feature_info(feature_set='standard'):
    """
    Get information about each feature in the set
    
    Args:
        feature_set: str - 'basic', 'standard', or 'complete'
    
    Returns:
        dict - Feature descriptions and typical ranges
    """
    
    info = {
        'heart_rate_bpm': {
            'name': 'Heart Rate',
            'unit': 'beats per minute',
            'typical_range': '60-100',
            'description': 'Resting heart rate - fastest way to detect stress/fitness'
        },
        'sdnn_ms': {
            'name': 'SDNN',
            'unit': 'milliseconds',
            'typical_range': '15-50',
            'description': 'Standard deviation of all heartbeats - overall heart variability'
        },
        'rmssd_ms': {
            'name': 'RMSSD',
            'unit': 'milliseconds',
            'typical_range': '20-50',
            'description': 'Parasympathetic activity - vagal tone/stress response'
        },
        'pnn50_percent': {
            'name': 'pNN50',
            'unit': 'percent',
            'typical_range': '0-50',
            'description': 'Percent of interval differences >50ms - parasympathetic indicator'
        },
        'pnn20_percent': {
            'name': 'pNN20',
            'unit': 'percent',
            'typical_range': '0-100',
            'description': 'Percent of interval differences >20ms - overall variability'
        },
        'sd1_ms': {
            'name': 'SD1',
            'unit': 'milliseconds',
            'typical_range': '10-30',
            'description': 'Poincaré plot SD1 - parasympathetic modulation'
        },
        'sd2_ms': {
            'name': 'SD2',
            'unit': 'milliseconds',
            'typical_range': '15-60',
            'description': 'Poincaré plot SD2 - long-term variability'
        },
        'lf_power': {
            'name': 'LF Power',
            'unit': 'milliseconds²',
            'typical_range': '100-1000',
            'description': 'Low frequency power - sympathetic/parasympathetic balance'
        },
        'hf_power': {
            'name': 'HF Power',
            'unit': 'milliseconds²',
            'typical_range': '50-500',
            'description': 'High frequency power - parasympathetic (vagal) activity'
        },
        'lf_hf_ratio': {
            'name': 'LF/HF Ratio',
            'unit': 'ratio',
            'typical_range': '1-4',
            'description': 'Sympathetic/parasympathetic balance - higher = more stress'
        }
    }
    
    # Return only info for selected features
    features_to_use = FEATURE_SETS[feature_set]
    return {f: info[f] for f in features_to_use if f in info}


def get_feature_names(feature_set='standard'):
    """Get list of feature names for the selected set"""
    return FEATURE_SETS.get(feature_set, [])


def get_feature_count(feature_set='standard'):
    """Get number of features in the selected set"""
    return len(FEATURE_SETS.get(feature_set, []))


def print_feature_summary(metrics, feature_set='standard'):
    """
    Print a formatted summary of only important features
    
    Args:
        metrics: dict - Full metrics from analyse.compute_metrics()
        feature_set: str - 'basic', 'standard', or 'complete'
    """
    
    selected = select_features(metrics, feature_set)
    info = get_feature_info(feature_set)
    
    print("\n" + "="*70)
    print(f"ML FEATURES - {feature_set.upper()} SET ({len(selected)} features)")
    print("="*70)
    
    for feature_name, value in selected.items():
        if feature_name in info:
            feature_info = info[feature_name]
            print(f"\n✓ {feature_info['name']}")
            print(f"  Value: {value} {feature_info['unit']}")
            print(f"  Range: {feature_info['typical_range']}")
            print(f"  Role: {feature_info['description']}")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    # Example usage
    from analyse import compute_metrics
    from digitize import ecg_to_csv
    
    print("Testing ML Feature Selector...")
    
    # Get metrics
    csv_path = ecg_to_csv(None)
    all_metrics = compute_metrics(csv_path)
    
    print(f"\n📊 Total metrics available: {len(all_metrics)}")
    print(f"   Metrics: {list(all_metrics.keys())}")
    
    # Show each feature set
    for set_name in ['basic', 'standard', 'complete']:
        features = select_features(all_metrics, set_name)
        print(f"\n✓ {set_name.upper()}: {len(features)} features")
        print(f"  {list(features.keys())}")
    
    # Print detailed summary for standard set
    print_feature_summary(all_metrics, 'standard')
