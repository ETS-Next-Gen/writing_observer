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
    # language
    ('Academic Language', 'Token', 'is_academic', None, 'percent'), # 1545
    ('Informal Language', 'Token', 'vwp_interactive', None, 'percent'), #1536
    ('Latinate Words', 'Token', 'is_latinate', None, 'percent'), # 1557
    ('Opinion Words', 'Token', 'vwp_evaluation', None, 'total'),
    ('Emotion Words', 'Token', 'vwp_emotionword', None, 'percent'), # how does this compare to vwp_emotion_states with doc
    # TODO explicity argument words vwp_exclicit_argument
    # TODO argumentation? vwp_argumentation
    ('Argument Words', 'Token', 'vwp_argumentword', None, 'percent'),
    # TODO statement of opinion vwp_statements_of_opinion
    # TODO statement of fact vwp_statements_of_fact
    # Transitions
    ('Transition Words', 'Doc', 'transitions', None, 'counts'),
    ('Positive Transition Words', 'Doc', 'transitions',[('==',['positive'])], 'total'),
    ('Conditional Transition Words', 'Doc', 'transitions',[('==',['conditional'])], 'total'),
    ('Consequential Transition Words', 'Doc', 'transitions',[('==',['consequential'])], 'total'),
    ('Contrastive Transition Words', 'Doc', 'transitions',[('==',['contrastive'])], 'total'),
    ('Counterpoint Transition Words', 'Doc', 'transitions',[('==',['counterpoint'])], 'total'),
    ('Comparative Transition Words', 'Doc', 'transitions',[('==',['comparative'])], 'total'),
    ('Cross Referential Transition Words', 'Doc', 'transitions',[('==',['crossreferential'])], 'total'),
    ('Illustrative Transition Words', 'Doc', 'transitions',[('==',['illustrative'])], 'total'),
    ('Negative Transition Words', 'Doc', 'transitions',[('==',['negative'])], 'total'),
    ('Emphatic Transition Words', 'Doc', 'transitions',[('==',['emphatic'])], 'total'),
    ('Evenidentiary Transition Words', 'Doc', 'transitions',[('==',['evidentiary'])], 'total'),
    ('General Transition Words', 'Doc', 'transitions',[('==',['general'])], 'total'),
    ('Ordinal Transition Words', 'Doc', 'transitions',[('==',['ordinal'])], 'total'),
    ('Purposive Transition Words', 'Doc', 'transitions',[('==',['purposive'])], 'total'),
    ('Periphrastic Transition Words', 'Doc', 'transitions',[('==',['periphrastic'])], 'total'),
    ('Hypothetical Transition Words', 'Doc', 'transitions',[('==',['hypothetical'])], 'total'),
    ('Summative Transition Words', 'Doc', 'transitions',[('==',['summative'])], 'total'),
    ('Introductory Transition Words', 'Doc', 'transitions',[('==',['introductory'])], 'total'),
    # pos_
    ('Adjectives', 'Token', 'pos_', [('==',['ADJ'])], 'percent'),
    ('Adverbs', 'Token', 'pos_', [('==',['ADV'])], 'percent'),
    ('Nouns', 'Token', 'pos_', [('==',['NOUN'])], 'percent'),
    ('Proper Nouns', 'Token', 'pos_', [('==',['PROPN'])], 'percent'),
    ('Verbs', 'Token', 'pos_', [('==',['VERB'])], 'percent'),
    ('Numbers', 'Token', 'pos_', [('==',['NUM'])], 'percent'),
    ('Prepositions', 'Token', 'pos_', [('==',['ADP'])], 'percent'),
    ('Coordinating Conjunction', 'Token', 'pos_', [('==',['CCONJ'])], 'percent'),
    ('Subordinating Conjunction', 'Token', 'pos_', [('==',['SCONJ'])], 'percent'),
    ('Auxiliary Verb', 'Token', 'pos_', [('==',['AUX'])], 'percent'),
    ('Pronoun', 'Token', 'pos_', [('==',['PRON'])], 'percent'),
    # sentence variety
    ('Sentence Types', 'Doc', 'sentence_types', None, 'counts'),
    ('Simple Sentences', 'Doc', 'sentence_types',[('==',['Simple'])], 'total'), # 1740
    ('Simple with Complex Predicates', 'Doc', 'sentence_types',[('==',['SimpleComplexPred'])], 'total'),
    ('Simple with Compound Predicates', 'Doc', 'sentence_types',[('==',['SimpleCompoundPred'])], 'total'),
    ('Simple with Compound Complex Predicates', 'Doc', 'sentence_types',[('==',['SimpleCompoundComplexPred'])], 'total'),
    ('Compound Sentences', 'Doc', 'sentence_types',[('==',['Compound'])], 'total'),
    ('Complex Sentences', 'Doc', 'sentence_types',[('==',['Complex'])], 'total'),
    ('Compound Complex Sentences', 'Doc', 'sentence_types',[('==',['CompoundComplex'])], 'total'),
    # Sources/Attributes/Citations/Quotes
    ('Information Sources', 'Token', 'vwp_source', None, 'percent'),
    ('Attributions', 'Token', 'vwp_attribution', None, 'percent'),
    ('Citations', 'Token', 'vwp_cite', None, 'percent'),
    ('Quoted Words', 'Token', 'vwp_quoted', None, 'percent'),
    # Dialogue
    # TODO text_with_ws
    # TODO vwp_direct_speech
    # TODO vwp_quoted - already used above
    # tone
    ('Positive Tone', 'Token', 'vwp_tone', [('>',[.4])], 'percent'),
    ('Negative Tone', 'Token', 'vwp_tone', [('<',[-.4])], 'percent'),
    # details
    ('Concrete Details', 'Token', 'concrete_details', None, 'percent'),
    ('Main Idea Sentences', 'Doc', 'main_ideas', None, 'total'), # check
    ('Supporting Idea Sentences', 'Doc', 'supporting_ideas', None, 'total'), # check
    ('Supporting Detail Sentences', 'Doc', 'supporting_details', None, 'total'), # check
    # Other items
    ('Polysyllabic Words', 'Token', 'nSyll', [('>',[3])], 'percent'), # 1676
    ('Low Frequency Words', 'Token', 'max_freq', [('<',[4])], 'percent'), # 1597
    ('Sentences', 'Doc', 'sents', None, 'total'), # 1412
    ('Paragraphs', 'Doc', 'delimiter_\n', None, 'total'), # 1415
    ('Character Trait Words', 'Token', 'vwp_character', None, 'percent'), # how does this compare to vwp_character_traits?
    # Scene and settings
    # TODO transition_category - duplicated above?
    # TODO vwp_in_direct_speech
    # TODO in_past_tense_scope
    # NEW ITEMS
    # TODO propositional attitudes, vwp_propositional_attitudes
    # TODO vwp_social_awareness
    # TODO own vs other, does not use AWE_INFO
    # TODO characters, uses NOMINALREFERENCES not AWE_INFO
]

# Create indicator dict to easily refer to each tuple above by name
# if a filter exists, we use a lowercased version of the label
# otherwise, we just use the indicator name (adjectives and adverbs both use pos_ for the indicator)
INDICATORS = {}
for indicator in SPAN_INDICATORS:
    if indicator[3] is None:
        name = indicator[2]
    else:
        name = indicator[0].lower().replace(' ', '_')
    indicator = indicator + (name,)
    INDICATORS[name] = indicator
