import copy
import xml.etree.ElementTree as ET

import learning_observer.util


RULE_PRIORITIES = {
    'school': 10,
    'teacher': 20,
    'student': 30
}

def match_rule(condition, rule):
    '''Check if a dictionary of conditions match a rule.

    >>> match_rule({'a': 123, 'b': 456}, {'a': 123})
    True
    >>> match_rule({'a': 123, 'b': 456}, {'a': 123, 'c': 789})
    False
    '''
    if condition is None:
        condition = {}
    if len(rule) == 0:
        return True
    if all(condition.get(key) == value for key, value in rule.items()):
        return True
    return False


def determine_rule_priority(rule):
    '''Fetches the rule's priority based on the keys in the
    rule's specificity subobject.
    '''
    specifiers = rule['specificity'].keys()
    if 'priority' in specifiers:
        return rule['specifiers']['priority']
    max_priority = max(RULE_PRIORITIES.get(key, 0) for key in specifiers)
    return max_priority


def parse_config(file_path):
    # TODO make this consistent with the rest of the system
    with open(file_path, 'r') as file:
        lines = file.readlines()

    config_list = []
    current_dict = None
    specificity = None

    for line in lines:
        line = line.strip()
        # TODO support multi-line comments
        if not line or line.startswith('#'):  # Skip empty lines and comments
            continue

        if line.endswith('{'):
            key = line[:-1].strip()
            current_dict = {}

            if '[' in key and ']' in key:  # Check for indexed block with specificity
                key, specificity = key.split('[', 1)
                specificity = specificity[:-1]  # Remove the closing '{'
                specificity = {i.split('=')[0]: i.split('=')[1].strip().strip('"') for i in specificity.split(';')}

            if not key:
                config_list.append({'value': current_dict})
            else:
                config_list.append({'value': {key: current_dict}})
            if specificity:
                config_list[-1]['specificity'] = specificity
                specificity = None  # Reset for next block
        elif line == '}':
            current_dict = None
        else:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip(';')  # Remove quotes and semicolons

            if '.' in key:
                sub_keys = key.split('.')
                current_level = current_dict or {}
                for sub_key in sub_keys[:-1]:
                    current_level = current_level.setdefault(sub_key, {})
                current_level[sub_keys[-1]] = value
            else:
                current_dict[key] = value

    return config_list


def parse_xml_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    def parse_element(element):
        # This function will recursively parse XML elements
        # and convert them into a nested dictionary structure,
        # including attributes.
        element_dict = {}
        if element.attrib:
            max_prio_to_use = 0
            for att in element.attrib:
                element_dict[f'_{att}'] = element.attrib[att]
                if att in RULE_PRIORITIES:
                    max_prio_to_use = max(max_prio_to_use, RULE_PRIORITIES[att])
            element_dict['_priority'] = max_prio_to_use
        if element.text and element.text.strip():
            element_dict['_content'] = element.text.strip()

        for child in element:
            child_dict = parse_element(child)
            if child.tag in element_dict:
                # Handle multiple child elements with the same tag
                if not isinstance(element_dict[child.tag], list):
                    element_dict[child.tag] = [element_dict[child.tag]]
                element_dict[child.tag].append(child_dict)
            else:
                element_dict[child.tag] = child_dict

        return element_dict

    # Parse the root element and return the resulting dictionary
    return {root.tag: parse_element(root)}


class settingsRuleWrapper(dict):
    '''This is a wrapper to allow the settings dictionary to access
    different layers of a configuration based on rules imposed. The
    base `settings` are treated as the default.
    '''
    def __init__(self, settings):
        self.settings = settings

    def get(self, setting, default=learning_observer.util.MissingType.Missing, condition=None):
        '''This get is similar to `utils.get_nested_dict_value`
        '''
        if setting is None:
            return '' # Missing
        keys = setting.split('.')
        current_dict = copy.deepcopy(self.settings)
        value = None
        for key in keys:
            if key in current_dict:
                current_dict = current_dict[key]
            
            if '_content' in current_dict:
                value = current_dict['_content']
            if isinstance(current_dict, list):
                # TODO determine the appropriate item to grab from list
                current_dict = self.fetch_appropriate_item(current_dict, condition)
        return value

    def fetch_appropriate_item(self, d, condition):
        '''We iterate over the rules to find any matching items. We
        sort them by priority then iterate over them to find the first
        instance of the `setting` we are trying to locate.
        '''
        sort_d = sorted(d, key=lambda x: x.get('_priority', 0), reverse=True)
        value = None
        for setting in sort_d:
            # check that
            print(setting)
            if match_rule(condition, {k.strip('_'): v for k, v in setting.items() if k.strip('_') in RULE_PRIORITIES}):
                value = setting
                break
        return value

def merge_dicts(default_dict, local_dict):
    def merge(a, b, path=None):
        print('***', a, b)
        if path is None:
            path = []
        for key in b:
            print(key, b[key])
            if key in a:
                print(a[key])
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    merge(a[key], b[key], path + [str(key)])
                elif isinstance(a[key], list) or isinstance(b[key], list):
                    pass
                    merged_lists = merge_lists(a[key], b[key])
                    a[key] = merged_lists
                else:
                    a[key] = b[key]
            else:
                a[key] = b[key]
        return a
    
    def merge_lists(a, b):
        list_a = a if isinstance(a, list) else [a]
        list_b = b if isinstance(b, list) else [b]

        merged_dict = {}
        # Function to get a merge key based on '_teacher' or '_school'
        def get_key(item):
            specifiers = ['_teacher', '_school', '_student']
            key = ''
            for spec in specifiers:
                if item.get(spec):
                    key += f'{spec}={item.get(spec)};'
            return key if len('key') > 0 else None

        # Add items from list1
        for item in list_a:
            key = get_key(item)
            if key is not None:
                merged_dict[key] = item
            else:
                # Handle items without '_teacher' or '_school'
                merged_dict['baseline'] = item

        # Update items from list2
        for item in list_b:
            key = get_key(item)
            if key is not None:
                merged_dict[key] = item
            else:
                # Handle items without '_teacher' or '_school'
                merged_dict['baseline'] = item

        return list(merged_dict.values())

    merged = merge(default_dict, local_dict)
    return merged


if __name__ == '__main__':
    # defaults = parse_config('defaults.locfg')
    # print(defaults)
    # local = parse_config('local.locfg')
    # print(local)
    import json
    defaults = parse_xml_file('defaults.lo.xml')
    print(json.dumps(defaults, indent=2))
    local = parse_xml_file('local.lo.xml')
    print(json.dumps(local, indent=2))
    merged_dict = merge_dicts(defaults, local)
    print(json.dumps(merged_dict, indent=2))

    settings = settingsRuleWrapper(merged_dict['config'])
    print(settings.get('roster_data.source'))
    print(settings.get('roster_data.source', condition={'teacher': '1234'}))
    print(settings.get('roster_data.source', condition={'school': '1234'}))
