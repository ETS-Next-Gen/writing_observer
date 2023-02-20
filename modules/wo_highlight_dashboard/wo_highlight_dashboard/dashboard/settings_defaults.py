'''
Defaults for different essay types
'''
argumentative = {
    'sort_by': {
        'options': ['is_academic', 'vwp_source', 'vwp_attribution', 'vwp_cite', 'vwp_interactive', 'vwp_argumentword', 'vwp_evaluation'],
        'selected': []
    },
    'metrics': {
        'options': ['sentences', 'paragraphs', 'pos_'],
        'selected': ['sentences', 'paragraphs']
    },
    'text': {
        'options': ['student_text'],
        'selected': 'student_text'
    },
    'highlight': {
        'options': [
            'main_idea_sentences', 'supporting_idea_sentences', 'supporting_detail_sentences',
            'informal_language', 'argument_words',
            'statements_of_opinion', 'statements_of_fact',
            'direct_speech_verbs', 'indirect_speech_quotation',
            'in_past_tense', 'propositional_attitudes', 'social_awareness',
            'transitions',
        ],
        'selected': ['main_idea_sentences']
    },
    'indicators': {
        'options': ['academic_language', 'informal_language', 'argument_words', 'latinate_words', 'information_sources', 'attributions', 'citations'],
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
