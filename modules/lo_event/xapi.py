"""
This is an interface to the XAPI registry of vocabulary.

This code parses JSON files and creates enum-like objects with mappings from cleaned names to original names and full objects.

For this to work, you should first download the .json files with the download_xapi_json.sh script in the xapi directory.

Example usage:
```python
import xapi

# Access the enum-like objects:
print(dir(xapi.ACTIVITYTYPE))
print(xapi.ACTIVITYTYPE.QUESTION)
print(xapi.ActivitytypeObjects.QUESTION)
```
"""

import json
import sys

sources = ["activityType", "attachmentUsage", "extension", "profile", "verb"]

for source in sources:
    json_data = json.load(open(f"xapi/{source}.json"))
    if source == "profile":
        selector = lambda x: x['name']
    else:
        get_us = lambda x: x.get('en-us', x.get('en-US', None))
        selector = lambda x: get_us(x['metadata']['metadata']['name'])
    names = [selector(d) for d in json_data]
    names_cleaned=[
        n.upper().strip().replace(' ', '_').replace('-', '_').replace('.', '_').replace('(', '').replace(')', '')
        for n in names
    ]
    
    # Create object to map names back to themselves
    class EnumMap:
        pass
    enum_map = EnumMap()
    setattr(sys.modules[__name__], source.upper(), enum_map)
    for i, name in enumerate(names):
        setattr(enum_map, names_cleaned[i], name)

    class ObjectMap:
        pass
    object_map = ObjectMap()
    # Create object to map names back to full object
    setattr(sys.modules[__name__], f'{source.capitalize()}Objects', object_map)
    for i, obj in enumerate(json_data):
        setattr(object_map, names_cleaned[i], obj)

