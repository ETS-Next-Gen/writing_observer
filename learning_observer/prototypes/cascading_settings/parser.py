def parse_config(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    config_list = []
    current_dict = None
    specificity = None

    for line in lines:
        line = line.strip()
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

# Example usage
config = parse_config('main.css')
for rule in config:
    print(rule)
