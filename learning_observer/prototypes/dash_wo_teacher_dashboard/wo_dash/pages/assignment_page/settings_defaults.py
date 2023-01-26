'''
Defaults for different essay types
'''
argumentative = {
    'sort_by': {
        'options': ['is_academic', 'vwp_source', 'vwp_attribution', 'vwp_cite', 'vwp_interactive', 'vwp_argumentword', 'vwp_evaluation'],
        'selected': []
    },
    'metrics': {
        'options': ['sents', 'delimiter_\n', 'time_on_task', 'pos_'],
        'selected': ['time_on_task', 'sents']
    },
    'text': {
        'options': ['student_text'],
        'selected': 'student_text'
    },
    'highlight': {
        'options': ['main_ideas', 'supporting_ideas', 'supporting_details', 'transitions', 'vwp_interactive', 'vwp_argumentword'],
        'selected': ['main_ideas']
    },
    'indicators': {
        'options': ['is_academic', 'vwp_source', 'vwp_attribution', 'vwp_cite', 'vwp_interactive', 'vwp_argumentword', 'vwp_evaluation'],
        'selected': []
    }
}
narrative = {
    'sort_by': {
        'options': [],
        'selected': []
    },
    'metrics': {
        'options': [],
        'selected': []
    },
    'text': {
        'options': ['student_text'],
        'selected': 'student_text'
    },
    'highlight': {
        'options': [],
        'selected': []
    },
    'indicators': {
        'options': [],
        'selected': []
    }
}
