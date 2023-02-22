'''
Each variable displays the defaults for each type of essay.
Ideally, users can select multiple (deep merge) to see both general
and argumentative for instance.

In the future, we probably want the dashboard more flexible with
different types of modules being plugged in (metrics/highlighter/etc.).
This information will probably want to be handled a bit nicer once
we understand the full workflow of the plugability.
'''
general = {
    'sort_by': {
        'options': [],
        'selected': []
    },
    'metrics': {
        'options': ['sentences', 'paragraphs', 'pos_'],
        'selected': ['prepositions']
    },
    'highlight': {
        'options': [
            'informal_language', 'transition_words', 'low_frequency_words',
            'positive_tone', 'negative_tone',
            'polysyllabic_words'
        ],
        'selected': ['transition_words', 'informal_language']
    },
    'indicators': {
        'options': [
            'academic_language', 'informal_language', 'latinate_words',
            'polysyllabic_words', 'low_frequency_words'
        ],
        'selected': ['informal_language']
    }
}
argumentative = {
    'sort_by': {
        'options': [],
        'selected': []
    },
    'metrics': {
        'options': [],
        'selected': []
    },
    'highlight': {
        'options': [
            'main_idea_sentences', 'supporting_idea_sentences', 'supporting_detail_sentences',
            'argument_words', 'explicit_argument',
            'statements_of_opinion', 'statements_of_fact',
            'explicit_claims',
        ],
        'selected': ['main_idea_sentences']
    },
    'indicators': {
        'options': ['opinion_words', 'argument_words', 'information_sources', 'attributions', 'citations'],
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
    'highlight': {
        'options': [
            'direct_speech_verbs', 'indirect_speech',
            'in_past_tense', 'social_awareness',
            'character_trait_words', 'concrete_details'
        ],
        'selected': []
    },
    'indicators': {
        'options': ['emotion_words', 'character_trait_words'],
        'selected': []
    }
}
source_based = {
    'sort_by': {
        'options': [],
        'selected': []
    },
    'metrics': {
        'options': [],
        'selected': []
    },
    'highlight': {
        'options': ['information_sources', 'attributions', 'citations', 'quoted_words'],
        'selected': []
    },
    'indicators': {
        'options': [],
        'selected': []
    }
}
