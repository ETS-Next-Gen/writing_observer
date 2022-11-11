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

# Short stories, from GPT-3

EXAMPLE_TEXTS =["""The snail had always dreamed of going to space. It was a lifelong dream, and finally, the day had arrived. The snail was strapped into a rocket, and prepared for takeoff.

As the rocket blasted off, the snail felt a sense of exhilaration. It was finally achieving its dream! The snail looked out the window as the Earth got smaller and smaller. Soon, it was in the vastness of space, floating weightlessly.

The snail was content, knowing that it had finally accomplished its dream. It would never forget this moment, floating in space, looking at the stars.
""",
"""One day, an old man was sitting on his porch, telling jokes to his grandson. The grandson was laughing hysterically at every joke.

Suddenly, a spaceship landed in front of them. A alien got out and said, "I come in peace! I come from a planet of intelligent beings, and we have heard that humans are the most intelligent beings in the universe. We would like to test your intelligence."

The old man thought for a moment, then said, "Okay, I'll go first. What has two legs, but can't walk?"

The alien thought for a moment, then said, "I don't know."

The old man chuckled and said, "A chair."
""",
"""The boy loved dolls. He loved their soft skin, their pretty clothes, and the way they always smelled like roses. He wanted to be a doll himself, so he could be pretty and perfect like them.

One day, he found a doll maker who promised to make him into a doll. The boy was so excited, and couldn't wait to become a doll.

The doll maker kept her promise, and the boy became a doll. He was perfect in every way, and he loved it. He loved being pretty and perfect, and he loved the way everyone fussed over him and treated him like a delicate little thing.

The only problem was that the boy's soul was now trapped inside the doll's body, and he could never be human again.
""",
"""The mouse had been hunting the cat for days. It was a big cat, twice her size, with sharp claws and teeth. But the mouse was determined to catch it.

Finally, she corner the cat in an alley. The cat hissed and slashed at the mouse, but the mouse was quick. She dart to the side and bit the cat's tail.

The cat yowled in pain and fled, and the mouse triumphantly went home with her prize.
""",
"""When I was younger, I dreamt of scaling Mt. Everest. It was the tallest mountain in the world, and I wanted to conquer it.

But then I was in a car accident that left me paralyzed from the waist down. I was confined to a wheelchair, and my dreams of scaling Everest seemed impossible.

But I didn't give up. I trained my upper body to be stronger, and I developed a special wheelchair that could handle the rough terrain.

Finally, after years of preparation, I made it to the top of Everest. It was the hardest thing I'd ever done, but I did it. And it was the best feeling in the world.
""",
"""The cucumber and the salmon were both new to the tank. The cucumber was shy and withdrawn, while the salmon was outgoing and friendly.

The salmon swim over to the cucumber and said hi. The cucumber was surprised, but happy to have made a new friend.

The two of them became fast friends, and they loved spending time together. The salmon would swim around the cucumber, and the cucumber would wrap itself around the salmon. They were both happy to have found a friend in the other.
""",
"""
"I can't believe we're all going to different colleges," said Sarah.

"I know," said John. "It's going to be weird not seeing you guys every day."

"But it's not like we're never going to see each other again," said Jane. "We can still visit each other, and keep in touch."

"I'm going to miss you guys so much," said Sarah.

"We're going to miss you too," said John.

"But we'll always be friends," said Jane.
"""
]
