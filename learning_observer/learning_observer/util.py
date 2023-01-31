'''
Random helper functions.

Design invariant:

* This should not rely on anything in the system.

We can relax the design invariant, but we should think carefully
before doing so.
'''

import math
import re


def paginate(data_list, nrows):
    '''
    Paginate list `data_list` into `nrows`-item rows.

    This should move into the client
    '''
    return [
        data_list[i * nrows:(i + 1) * nrows]
        for i in range(math.ceil(len(data_list) / nrows))
    ]


def to_safe_filename(name):
    '''
    Convert a name to a filename. The filename escapes any non-alphanumeric
    characters, so there are no invalid or control characters.

    Can be converted back with `from_filename`

    For example, { would be encoded as -123- since { is character 123 in UTF-8.
    '''
    return ''.join(
        '-' + str(ord(c)) + '-' if not c.isidentifier() and not c.isalnum() else c
        for c in name
    )


def from_safe_filename(filename):
    '''
    Convert a filename back to a name.

    See `to_filename` for more information.

    Uses `re`, uncompiled, so probably not very fast. Right now, this is used
    for testing / debugging, but might be worth optimizing if we ever use it
    otherwise.
    '''
    return re.sub(r'-(\d+)-', lambda m: chr(int(m.group(1))), filename)


def url_pathname(s):
    """
    Remove URL and domain from a URL. Return the full remainder of the path.

    Input: https://www.googleapis.com/drive/v3/files
    Output: drive/v3/files

    Note that in contrast to the JavaScript version, we don't include the
    initial slash.
    """
    return s.split('/', 3)[-1]


def translate_json_keys(d, translations):
    """
    Replace all of the keys in the dictionary with new keys, including
    sub-dictionaries. This was written for converting CamelCase from
    Google APIs to snake_case.

    Note that this mutates the original data structure
    """
    if isinstance(d, list):
        for item in d:
            translate_json_keys(item, translations)
    elif isinstance(d, dict):
        for k, v in list(d.items()):
            if k in translations:
                d[translations[k]] = d.pop(k)
            else:
                pass  # print("UNTRANSLATED KEY: ", k)

            if isinstance(v, dict) or isinstance(v, list):
                translate_json_keys(v, translations)
    return d


# And a test case
if __name__ == '__main__':
    assert to_safe_filename('{') == '-123-'
    assert from_safe_filename('-123-') == '{'
    test_string = "Hello? How are -- you doing? łłł"
    assert from_safe_filename(to_safe_filename(test_string)) == test_string
    assert url_pathname('https://www.googleapis.com/drive/v3/files') == 'drive/v3/files'
