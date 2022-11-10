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

# Two short stories, from GPT-3

EXAMPLE_TEXT_1 = """The snail had always dreamed of going to space. It was a lifelong dream, and finally, the day had arrived. The snail was strapped into a rocket, and prepared for takeoff.

As the rocket blasted off, the snail felt a sense of exhilaration. It was finally achieving its dream! The snail looked out the window as the Earth got smaller and smaller. Soon, it was in the vastness of space, floating weightlessly.

The snail was content, knowing that it had finally accomplished its dream. It would never forget this moment, floating in space, looking at the stars.
"""

EXAMPLE_TEXT_2 = """One day, an old man was sitting on his porch, telling jokes to his grandson. The grandson was laughing hysterically at every joke.

Suddenly, a spaceship landed in front of them. A alien got out and said, "I come in peace! I come from a planet of intelligent beings, and we have heard that humans are the most intelligent beings in the universe. We would like to test your intelligence."

The old man thought for a moment, then said, "Okay, I'll go first. What has two legs, but can't walk?"

The alien thought for a moment, then said, "I don't know."

The old man chuckled and said, "A chair."
"""