'''
Random helper functions.

Design invariant:

* This should not rely on anything in the system.

We can relax the design invariant, but we should think carefully
before doing so.
'''

import math


def paginate(data_list, nrows):
    '''
    Paginate list `data_list` into `nrows`-item rows.

    This should move into the client
    '''
    return [
        data_list[i * nrows:(i + 1) * nrows]
        for i in range(math.ceil(len(data_list) / nrows))
    ]
