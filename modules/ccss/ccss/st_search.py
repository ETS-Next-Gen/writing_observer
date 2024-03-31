'''
This implements a search for a particular standard using a
relatively small, fast neural network.

Load time is a little bit annoying (3-4 seconds), but queries
run quickly.

It can be used directly, or to return a set of all possible
results, with the final results then pruned by an LLM

Perhaps this ought to be teased out into its own library. This should
definitely not be placed in anything imported in __init__.py or
ccss.py, since most uses of ccss probably won't use this, and it adds
to startup time.
'''

import json

from sentence_transformers import SentenceTransformer, util
import torch

# Load the model. This is a relatively small model (80MB)
model = SentenceTransformer('all-MiniLM-L6-v2')

standard_texts = list(json.load(open("ccss.json")).values())

# Encode all standard_texts to get their embeddings
embeddings = model.encode(standard_texts, convert_to_tensor=True)

def search(query, result_count):
    # Encode the query
    query_embedding = model.encode(query, convert_to_tensor=True)

    # Use cosine similarity to find the most similar standard_texts to the query
    cos_similarities = util.pytorch_cos_sim(query_embedding, embeddings)[0]

    # Get the index of the most similar sentence
    top_match_index = torch.argmax(cos_similarities).item()
    top_N_match_indices = cos_similarities.argsort(descending=True)[:result_count]
    
    result_standard_texts = [standard_texts[i] for i in top_N_match_indices]
    return result_standard_texts

if __name__ == '__main__':
    for result in search("division", 10):
        print(result)
