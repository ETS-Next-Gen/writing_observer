# Define a set of indicators with the kind of filtering/summariation we want
#
# Academic Language, Latinate Words, Low Frequency Words, Adjectives, Adverbs,
#    Sentences, Paragraphs -- 
#    just need to have lexicalfeatures in the pipeline to run.
#
# Transition Words, Ordinal Transition Words --
#    -- shouldonly need syntaxdiscoursefeats in the pipeline to run
#
# Information Sources, Attributions, Citations, Quoted Words, Informal Language
# Argument Words, Emotion Words, Character Trait Words, Concrete Details --
#     Need lexicalfeatures + syntaxdiscoursefeats + viewpointfeatures to run
#
# Main idea sentences, supporting idea sentences, supporting detail sentences --
#     Need the full pipeline to run, though the main dependencies are on
#     lexicalclusters and contentsegmentation
#
# Format for this list: Label, type of indicator (Token or Doc), indicator name,
# filter (if needed), summary function to use
SPAN_INDICATORS = [
    ('Academic Language', 'Token', 'is_academic', None, 'percent'),
    ('Latinate Words', 'Token', 'is_latinate', None, 'percent'),
    ('Polysyllabic Words', 'Token', 'nSyll', [('>',[3])], 'percent'),
    ('Low Frequency Words', 'Token', 'max_freq', [('<',[4])], 'percent'),
    ('Transition Words', 'Doc', 'transitions', None, 'counts'),
    ('Ordinal Transition Words', 'Doc', 'transitions',[('==',['ordinal'])], 'total'),
    ('Adjectives', 'Token', 'pos_', [('==',['ADJ'])], 'percent'),
    ('Adverbs', 'Token', 'pos_', [('==',['ADV'])], 'percent'),
    ('Sentence Types', 'Doc', 'sentence_types', None, 'counts'),
    ('Simple Sentences', 'Doc', 'sentence_types',[('==',['Simple'])], 'total'),
    ('Sentences', 'Doc', 'sents', None, 'total'),
    ('Paragraphs', 'Doc', 'delimiter_\n', None, 'total'),
    ('Information Sources', 'Token', 'vwp_source', None, 'percent'),
    ('Attributions', 'Token', 'vwp_attribution', None, 'percent'),
    ('Citations', 'Token', 'vwp_cite', None, 'percent'),
    ('Quoted Words', 'Token', 'vwp_quoted', None, 'percent'),
    ('Informal Language', 'Token', 'vwp_interactive', None, 'percent'),
    ('Argument Words', 'Token', 'vwp_argumentword', None, 'percent'),
    ('Opinion Words', 'Token', 'vwp_evaluation', None, 'total'),
    ('Emotion Words', 'Token', 'vwp_emotionword', None, 'percent'),
    ('Positive Tone', 'Token', 'vwp_tone', [('>',[.4])], 'percent'),
    ('Negative Tone', 'Token', 'vwp_tone', [('<',[-.4])], 'percent'),
    ('Character Trait Words', 'Token', 'vwp_character', None, 'percent'),
    ('Concrete Details', 'Token', 'concrete_details', None, 'percent'),
    ('Main Idea Sentences', 'Doc', 'main_ideas', None, 'total'),
    ('Supporting Idea Sentences', 'Doc', 'supporting_ideas', None, 'total'),
    ('Supporting Detail Sentences', 'Doc', 'supporting_details', None, 'total')
]

INDICATORS = {}
for indicator in SPAN_INDICATORS:
    if indicator[3] is None:
        name = indicator[2]
    else:
        name = indicator[0].lower().replace(' ', '_')
    indicator = indicator + (name,)
    INDICATORS[name] = indicator
