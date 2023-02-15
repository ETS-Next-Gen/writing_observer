from recordclass import dataobject, asdict

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
    ('Academic Language', 'Token', 'is_academic', None, 'percent'),
    ('Informal Language', 'Token', 'vwp_interactive', None, 'percent'),
    ('Latinate Words', 'Token', 'is_latinate', None, 'percent'),
    ('Opinion Words', 'Token', 'vwp_evaluation', None, 'total'),
    ('Emotion Words', 'Token', 'vwp_emotionword', None, 'percent'),
    # vwp_emotion_states looks for noun/emotion word pairs (takes a lot of resources) - ignoring for now
    # Argumentation
    # ('Argumentation', 'Token', 'vwp_argumentation', None, 'percent'),  # most resource heavy - ignoring for now
    ('Argument Words', 'Token', 'vwp_argumentword', None, 'percent'),  # more surfacey # TODO needs new label
    ('Explicit argument', 'Token', 'vwp_explicit_argument', None, 'percent'),  # surfacey # TODO needs new label
    # statements
    ('Statements of Opinion', 'Doc', 'vwp_statements_of_opinion', None, 'percent'),
    ('Statements of Fact', 'Doc', 'vwp_statements_of_fact', None, 'percent'),
    # Transitions
    # eventually we want to exclude \n\n as transitions using `[('!=', ['introductory'])]`
    # however the introductory category also includes "let us" and "let's"
    # no highlighting is shown on the new lines, so we won't remove it for now.
    ('Transition Words', 'Doc', 'transitions', None, 'counts'),
    #
    ('Positive Transition Words', 'Doc', 'transitions', [('==', ['positive'])], 'total'),
    ('Conditional Transition Words', 'Doc', 'transitions', [('==', ['conditional'])], 'total'),
    ('Consequential Transition Words', 'Doc', 'transitions', [('==', ['consequential'])], 'total'),
    ('Contrastive Transition Words', 'Doc', 'transitions', [('==', ['contrastive'])], 'total'),
    ('Counterpoint Transition Words', 'Doc', 'transitions', [('==', ['counterpoint'])], 'total'),
    ('Comparative Transition Words', 'Doc', 'transitions', [('==', ['comparative'])], 'total'),
    ('Cross Referential Transition Words', 'Doc', 'transitions', [('==', ['crossreferential'])], 'total'),
    ('Illustrative Transition Words', 'Doc', 'transitions', [('==', ['illustrative'])], 'total'),
    ('Negative Transition Words', 'Doc', 'transitions', [('==', ['negative'])], 'total'),
    ('Emphatic Transition Words', 'Doc', 'transitions', [('==', ['emphatic'])], 'total'),
    ('Evenidentiary Transition Words', 'Doc', 'transitions', [('==', ['evidentiary'])], 'total'),
    ('General Transition Words', 'Doc', 'transitions', [('==', ['general'])], 'total'),
    ('Ordinal Transition Words', 'Doc', 'transitions', [('==', ['ordinal'])], 'total'),
    ('Purposive Transition Words', 'Doc', 'transitions', [('==', ['purposive'])], 'total'),
    ('Periphrastic Transition Words', 'Doc', 'transitions', [('==', ['periphrastic'])], 'total'),
    ('Hypothetical Transition Words', 'Doc', 'transitions', [('==', ['hypothetical'])], 'total'),
    ('Summative Transition Words', 'Doc', 'transitions', [('==', ['summative'])], 'total'),
    ('Introductory Transition Words', 'Doc', 'transitions', [('==', ['introductory'])], 'total'),
    # pos_
    ('Adjectives', 'Token', 'pos_', [('==', ['ADJ'])], 'total'),
    ('Adverbs', 'Token', 'pos_', [('==', ['ADV'])], 'total'),
    ('Nouns', 'Token', 'pos_', [('==', ['NOUN'])], 'total'),
    ('Proper Nouns', 'Token', 'pos_', [('==', ['PROPN'])], 'total'),
    ('Verbs', 'Token', 'pos_', [('==', ['VERB'])], 'total'),
    ('Numbers', 'Token', 'pos_', [('==', ['NUM'])], 'total'),
    ('Prepositions', 'Token', 'pos_', [('==', ['ADP'])], 'total'),
    ('Coordinating Conjunction', 'Token', 'pos_', [('==', ['CCONJ'])], 'total'),
    ('Subordinating Conjunction', 'Token', 'pos_', [('==', ['SCONJ'])], 'total'),
    ('Auxiliary Verb', 'Token', 'pos_', [('==', ['AUX'])], 'total'),
    ('Pronoun', 'Token', 'pos_', [('==', ['PRON'])], 'total'),
    # sentence variety
    ('Sentence Types', 'Doc', 'sentence_types', None, 'counts'),
    ('Simple Sentences', 'Doc', 'sentence_types', [('==', ['Simple'])], 'total'),
    ('Simple with Complex Predicates', 'Doc', 'sentence_types', [('==', ['SimpleComplexPred'])], 'total'),
    ('Simple with Compound Predicates', 'Doc', 'sentence_types', [('==', ['SimpleCompoundPred'])], 'total'),
    ('Simple with Compound Complex Predicates', 'Doc', 'sentence_types', [('==', ['SimpleCompoundComplexPred'])], 'total'),
    ('Compound Sentences', 'Doc', 'sentence_types', [('==', ['Compound'])], 'total'),
    ('Complex Sentences', 'Doc', 'sentence_types', [('==', ['Complex'])], 'total'),
    ('Compound Complex Sentences', 'Doc', 'sentence_types', [('==', ['CompoundComplex'])], 'total'),
    # Sources/Attributes/Citations/Quotes
    ('Information Sources', 'Token', 'vwp_source', None, 'percent'),
    ('Attributions', 'Token', 'vwp_attribution', None, 'percent'),
    ('Citations', 'Token', 'vwp_cite', None, 'percent'),
    ('Quoted Words', 'Token', 'vwp_quoted', None, 'percent'),
    # Dialogue
    ('Direct Speech Verbs', 'Doc', 'vwp_direct_speech', None, 'percent'),  # TODO needs new label
    ('Indirect Speech Quotation', 'Token', 'vwp_in_direct_speech', None, 'percent'),  # TODO needs new label
    # vwp_quoted - already used above
    # tone
    ('Positive Tone', 'Token', 'vwp_tone', [('>', [.4])], 'percent'),
    ('Negative Tone', 'Token', 'vwp_tone', [('<', [-.4])], 'percent'),
    # details
    ('Concrete Details', 'Token', 'concrete_details', None, 'percent'),
    ('Main Idea Sentences', 'Doc', 'main_ideas', None, 'total'),
    ('Supporting Idea Sentences', 'Doc', 'supporting_ideas', None, 'total'),
    ('Supporting Detail Sentences', 'Doc', 'supporting_details', None, 'total'),
    # Other items
    ('Polysyllabic Words', 'Token', 'nSyll', [('>', [3])], 'percent'),
    ('Low Frequency Words', 'Token', 'max_freq', [('<', [4])], 'percent'),
    ('Sentences', 'Doc', 'sents', None, 'total'),
    ('Paragraphs', 'Doc', 'delimiter_\n', None, 'total'),
    ('Character Trait Words', 'Token', 'vwp_character', None, 'percent'),
    ('In Past Tense', 'Token', 'in_past_tense_scope', None, 'percent'),
    ('Propositional Attitudes', 'Doc', 'vwp_propositional_attitudes', None, 'percent'),
    ('Social Awareness', 'Doc', 'vwp_social_awareness', None, 'percent')
]

# Create indicator dict to easily refer to each tuple above by name
INDICATORS = {}
INDICATOR_W_IDS = []
for indicator in SPAN_INDICATORS:
    id = indicator[0].lower().replace(' ', '_')
    INDICATOR_W_IDS.append((id, ) + indicator)
    INDICATORS[id] = (id, ) + indicator


class NLPIndicators(dataobject):
    id: str
    name: str
    type: str
    parent: str
    filters: list
    function: str
    # tooltip: str


indicators = map(lambda ind: NLPIndicators(*ind), INDICATOR_W_IDS)
INDICATOR_JSONS = [asdict(ind) for ind in indicators]
