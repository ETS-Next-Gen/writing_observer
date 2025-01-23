import copy
import learning_observer.settings
import writing_observer.nlp_indicators
import writing_observer.languagetool_features

parents = []

OPTIONS = [
    {'id': indicator['id'], 'types': {'highlight': {}, 'metric': {}}, 'label': indicator['name'], 'parent': indicator['category']}
    for indicator in writing_observer.nlp_indicators.INDICATOR_JSONS
]
for category, label in writing_observer.nlp_indicators.INDICATOR_CATEGORIES.items():
    OPTIONS.append({'id': category, 'label': label, 'parent': 'text_information'})
OPTIONS.append({'id': 'text_information', 'label': 'Text Information', 'parent': ''})


if learning_observer.settings.module_setting('writing_observer', 'use_languagetool'):
    for lt_item in writing_observer.languagetool_features.AVAILABLE_ITEMS:
        OPTIONS.append({'id': lt_item[1], 'types': {'highlight': {}, 'metric': {}}, 'label': lt_item[1], 'parent': lt_item[0]})
    for lt_category in writing_observer.languagetool_features.CATEGORIES:
        OPTIONS.append({'id': lt_category, 'label': lt_category, 'parent': 'text_error'})
    OPTIONS.append({'id': 'text_error', 'label': 'Text Errors', 'parent': ''})


# TODO currently each preset is the full list of options with specific
# values being set to true/including a color. We ought to just store
# the true values and their respective colors.
# Though if we keep the entire list in the preset, we can choose colors
# for non-true values before they are selected.

# Set of colors to use for highlighting with presets
HIGHLIGHTING_COLORS = [
    "#FFD700",  # Golden Yellow
    "#87CEEB",  # Sky Blue
    "#98FB98",  # Pale Green
    "#FFB6C1",  # Light Pink
    "#F0E68C",  # Khaki
    "#FF69B4",  # Hot Pink
    "#AFEEEE",  # Pale Turquoise
    "#FFA07A",  # Light Salmon
    "#D8BFD8",  # Thistle
    "#ADD8E6",  # Light Blue
    "#FFDEAD",  # Navajo White
    "#FA8072",  # Salmon
    "#E6E6FA",  # Lavender
    "#FFE4E1",  # Misty Rose
    "#F5DEB3"   # Wheat
]

# TODO these are used for creating the common presets
PRESETS_TO_CREATE = {
    'Narrative': ['direct_speech_verbs', 'indirect_speech', 'character_trait_words', 'in_past_tense', 'social_awareness'],
    'Argumentative': ['statements_of_opinion', 'statements_of_fact', 'information_sources', 'attributions', 'citations'],
    'Parts of Speech': ['adjectives', 'adverbs', 'nouns', 'proper_nouns', 'verbs', 'prepositions', 'coordinating_conjunction', 'subordinating_conjunction', 'auxiliary_verb', 'pronoun'],
    'Sentence Structure': ['simple_sentences', 'simple_with_complex_predicates', 'simple_with_compound_predicates', 'simple_with_compound_complex_predicates', 'compound_sentences', 'complex_sentences', 'compound_complex_sentences'],
    'Organization': ['main_idea_sentences', 'supporting_idea_sentences', 'supporting_detail_sentences'],
    'Tone': ['positive_tone', 'negative_tone', 'emotion_words', 'opinion_words'],
    'Vocabulary': ['academic_language', 'informal_language', 'latinate_words', 'polysyllabic_words', 'low_frequency_words']
}

deselect_all = 'Deselect All'
PRESETS = {deselect_all: OPTIONS}


def add_preset_to_presets(key, value):
    '''This function creates a copy of the options and
    sets each of the items in `value` to True along with
    a highlighted color. This is for creating presets
    from the `PRESETS_TO_CREATE` object.
    '''
    color_index = 0
    preset = copy.deepcopy(OPTIONS)
    for option in preset:
        if option['id'] in value:
            option['types']['highlight']['value'] = True
            option['types']['highlight']['color'] = HIGHLIGHTING_COLORS[color_index]
            color_index += 1

    PRESETS[key] = preset


# Add each preset to PRESETS
for k, v in PRESETS_TO_CREATE.items():
    add_preset_to_presets(k, v)
