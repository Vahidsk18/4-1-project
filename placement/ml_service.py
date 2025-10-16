# placement/ml_service.py

# NOTE: In a real project, this file would handle loading a trained model:
# import joblib
# MODEL = joblib.load('path/to/your/model.joblib')

def get_overall_placement_prediction(student_profile):
    """
    Mocks an overall placement prediction probability (0-100%)
    by scaling the existing Placement Readiness Score.
    
    This is what a real ML model would provide, but across the entire job market.
    """
    if student_profile.placement_readiness_score is None:
        return 0.0
        
    # Example: Scale readiness score (max 100) to prediction (max 95) 
    # to simulate a slight uncertainty in prediction.
    prediction = float(student_profile.placement_readiness_score) * 0.95
    return round(min(prediction, 100.0), 2)

def get_job_specific_prediction(job_match_percentage):
    """
    Generates a job-specific prediction (0-100%) based on the Match Score.
    
    This simulates a dedicated classification model that uses Job Match Score
    as its primary input.
    """
    if job_match_percentage >= 100:
        return 98.0
    elif job_match_percentage >= 75:
        return round(job_match_percentage * 0.90 + 10, 2)
    elif job_match_percentage >= 50:
        return round(job_match_percentage * 0.70 + 10, 2)
    else:
        return round(job_match_percentage * 0.50, 2)