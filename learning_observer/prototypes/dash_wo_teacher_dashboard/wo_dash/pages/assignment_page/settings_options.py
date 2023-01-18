'''
Defines the options in the settings panel
'''
# package imports
from dash import html
import dash_bootstrap_components as dbc

# currently we use the same options for both sorting and indicators
# sort_by_options = {
#     'is_academic': {'label': 'Academic Language', 'value': 'is_academic'},
#     'vwp_argumentword': {'label': 'Argument Language', 'value': 'vwp_argumentword'},
#     'vwp_attribution': {'label': 'Attributions', 'value': 'vwp_attribution'},
#     'vwp_cite': {'label': 'Citations', 'value': 'vwp_cite'},
#     'vwp_source': {'label': 'Information Sources', 'value': 'vwp_source'},
#     'vwp_interactive': {'label': 'Informal Language', 'value': 'vwp_interactive'},
#     'vwp_evaluation': {'label': 'Opinion Words', 'value': 'vwp_evaluation'}
# }
metric_options = {
    'sents': {
        'label': dbc.Badge(
            '# sentences',
            color='info',
            title='Total number of sentences'
        ),
        'value': 'sents'
    },
    'delimiter_\n': {
        'label': dbc.Badge(
            '# paragraphs',
            color='info',
            title='Total number of paragraphs'
        ),
        'value': 'delimiter_\n'
    },
    'pos_': {
        'label': dbc.Badge(
            '# adverbs',
            color='info',
            title='Total number of adverbs'
        ),
        'value': 'pos_'
    },
    'time_on_task': {
        'label': dbc.Badge(
            '# minutes on task',
            color='info',
            title='Total minutes on task'
        ),
        'value': 'time_on_task'
    }
}
text_options = {
    'student_text': {
        'label': 'Student text',
        'value': 'student_text'
    }
}
highlight_options = {
    'main_ideas': {
        'label': html.Span('Main ideas', className='main_ideas_highlight'),
        'value': 'main_ideas'
    },
    'supporting_ideas': {
        'label': html.Span('Supporting ideas', className='supporting_ideas_highlight'),
        'value': 'supporting_ideas'
    },
    'supporting_details': {
        'label': html.Span('Supporting details', className='supporting_details_highlight'),
        'value': 'supporting_details'
    },
    'transitions': {
        'label': html.Span('Ordinal Transition Words', className='transitions_highlight'),
        'value': 'transitions'
    },
    'vwp_interactive': {
        'label': html.Span('Informal Language', className='vwp_interactive_highlight'),
        'value': 'vwp_interactive'
    },
    'vwp_argumentword': {
        'label': html.Span('Argument Words', className='vwp_argumentword_highlight'),
        'value': 'vwp_argumentword'
    }
}
indicator_options = {
    'is_academic': {
        'label': html.Span(
            'Academic Language',
            title=''  # TODO fill the title in
        ),
        'value': 'is_academic'
    },
    'is_latinate': {
        'label': html.Span(
            'Latinate Words',
            title=''  # TODO fill the title in
        ),
        'value': 'is_latinate'
    },
    'vwp_source': {
        'label': html.Span(
            'Information Sources',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_source'
    },
    'vwp_attribution': {
        'label': html.Span(
            'Attributions',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_attribution'
    },
    'vwp_cite': {
        'label': html.Span(
            'Citations',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_cite'
    },
    'vwp_quoted': {
        'label': html.Span(
            'Quoted Words',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_quoted'
    },
    'vwp_interactive': {
        'label': html.Span(
            'Informal Language',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_interactive'
    },
    'vwp_argumentword': {
        'label': html.Span(
            'Argument Words',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_argumentword'
    },
    'vwp_evaluation': {
        'label': html.Span(
            'Opinion Words',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_evaluation'
    },
    'vwp_emotionword': {
        'label': html.Span(
            'Emotion Words',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_emotionword'
    },
    'vwp_tone': {
        'label': html.Span(
            'Negative Tone',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_tone'
    },
    'vwp_character': {
        'label': html.Span(
            'Character Trait Words',
            title=''  # TODO fill the title in
        ),
        'value': 'vwp_character'
    },
    'concrete_details': {
        'label': html.Span(
            'Concrete Details',
            title=''  # TODO fill the title in
        ),
        'value': 'concrete_details'
    }
}
