def create_default_metadata(name, error_message):
    """Helper function to create default metadata with error information"""
    return {
        'project_name': name,
        'project_description': error_message,
        'project_structure': [],
        'key_features': [],
        'project_tasks': ['Resolve AI response parsing error'],
        'implemented_features': [],
        'planned_features': [],
        'feature_priorities': {
            'high': [],
            'medium': [],
            'low': []
        },
        'validation_notes': [error_message]
    }
