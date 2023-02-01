'''
This is a set of helpers to assist in development of the Writing Observer. It is
not really intended to be used in a production system, so much as in development,
testing, etc.

It provides things like:
- Dummy NLP functions which can tag random text
- Simplified NLP algorithms
- Nice ways to render data

This can work without all of the tooling, load time, etc. required for the full
AWE Workbench, and should make development faster and easier.
'''

import loremipsum
import random
import re


def limited_sample(total, n):
    '''
    Similar to random.sample, but:
    - with smooth degradation if we don't have enough data.
    - Returns sorted
    '''
    return sorted(random.sample(range(total), min(total, n)))


def select_random_segments(text, segments=3, segment_length=3, seed=0):
    '''
    Select random segments of words from the input sentence.

    Parameters:
        sentence (str): The input sentence to select segments from.
        segments (int, optional): The number of segments to select. Defaults to 3.
        segment_length (int, optional): The maximum length of each segment in words. If None, there is no maximum length. Defaults to None.
        seed: An optional random number seed. Set to `None` to be truly random. Otherwise, as as text fixture, it's deterministic.

    Returns:
        list: A list of tuples, each containing the start and end indices of a selected segment.
    '''
    if seed is not None:
        state = random.getstate()
        random.seed(seed)
    word_boundaries = [match.start() for match in re.finditer(r"\b\w+\b", text)]
    word_boundary_count = len(word_boundaries)
    selected_indices = limited_sample(word_boundary_count - segment_length, segments)
    segments_positions = [(word_boundaries[index], word_boundaries[index + segment_length]) for index in selected_indices]
    if seed is not None:
        random.setstate(state)
    return segments_positions


def select_random_words(sentence, segments=3):
    '''
    Select random words from the input sentence.

    Parameters:
        sentence (str): The input sentence to select words from.
        segments (int, optional): The number of words to select. Defaults to 3.

    Returns:
        list: A list of tuples, each containing the start and end indices of a selected word.
    '''
    word_boundaries = [match.start() for match in re.finditer(r"\b\w+\b", sentence)]
    word_boundary_count = len(word_boundaries)
    selected_indices = limited_sample(word_boundary_count, segments)
    word_positions = [(word_boundaries[index], word_boundaries[index] + len(sentence[word_boundaries[index]:].split()[0])) for index in selected_indices]
    return word_positions


def select_random_sentences(text, segments=3):
    '''
    Select random sentences from the input text.

    Parameters:
        text (str): The input text to select sentences from.
        segments (int, optional): The number of sentences to select. Defaults to 3.

    Returns:
        list: A list of tuples, each containing the start and end indices of a selected sentence.
    '''
    sentence_boundaries = [match.start() for match in re.finditer(r"[.?!][\s\S]*", text)]
    sentence_boundary_count = len(sentence_boundaries)
    selected_indices = limited_sample(sentence_boundary_count - 1, segments)
    sentence_positions = [(sentence_boundaries[index], sentence_boundaries[index + 1]) for index in selected_indices]
    return sentence_positions


def show_selections(text, segments):
    '''
    Extract the selected text segments from a piece of text.

    Parameters:
        text (str): The input text from which to extract the segments.
        segments (list): A list of tuples, each containing the start and end indices of a selected segment.

    Returns:
        list: A list of strings, each representing a selected segment of the input text.
    '''
    return [text[a:b] for a, b in segments]


def lorem(paragraphs=5):
    '''
    Generate lorem ipsum test text.
    '''
    return "\n\n".join(loremipsum.get_paragraphs(paragraphs))


TRANSITION_WORDS = ["also", "as well", "besides", "furthermore", "in addition", "in fact",    "indeed", "likewise", "moreover", "similarly", "too", "additionally",    "again", "alternatively", "and", "as", "as a result", "as an example",    "as a consequence", "as a matter of fact", "as well as", "at the same time",    "because", "before", "being that", "by comparison", "by contrast",    "by the same token", "compared to", "conversely", "correspondingly",    "coupled with", "earlier", "equally", "for instance", "for example",    "for that reason", "further", "furthermore", "hence", "however",    "in comparison", "in contrast", "in like manner", "in similar fashion",    "in the same way", "incidentally", "indeed", "instead", "likewise",    "meanwhile", "moreover", "namely", "neither", "nevertheless",    "next", "nonetheless", "nor", "not only", "not to mention",    "on the contrary", "on the other hand", "oppositely", "or", "otherwise",    "overall", "particularly", "previously", "rather", "regardless",    "similarly", "so", "so as to", "then", "therefore", "thus", "ultimately",    "unlike", "while"]


def find_keywords_in_text(text, keywords):
    """
    Finds all instances of the keywords in the text and returns a set of start and end indices for each match.

    Parameters:
    text (str): The text to search in.
    keywords (list): A list of keywords to search for in the text.

    Returns:
    set: A set of start and end indices for each match of a keyword in the text.
    """
    keywords_regex = "|".join(r"\b" + word + r"\b" for word in keywords)
    keyword_matches = [(match.start(), match.end()) for match in re.finditer(keywords_regex, text, flags=re.IGNORECASE)]
    return set(keyword_matches)
