import copy
import writing_observer

parents = []

OPTIONS = [
    {'id': indicator['id'], 'types': {'highlight': {}, 'metric': {}}, 'label': indicator['name'], 'parent': 'text-information'}
    for indicator in writing_observer.nlp_indicators.INDICATOR_JSONS
]
OPTIONS.append({'id': 'text-information', 'label': 'Text Information', 'parent': ''})

# TODO create meaningful presets. Paul provided me with some ideas for
# presets to create.
# TODO currently each preset is the full list of options with specific
# values being set to true/including a color. We ought to just store
# the true values and their respective colors.
# Though if we keep the entire list in the preset, we can choose colors
# for non-true values before they are selected.

# TODO remove this function. it is sample code for creating fake presets
def create_preset(options, is_even=True):
    preset = copy.deepcopy(options)
    for i, o in enumerate(preset):
        # if i % 2 == 0 if is_even else 1:
        if i % 2 == (0 if is_even else 1):
            continue
        if 'types' in o:
            o['types']['highlight']['value'] = True
            o['types']['highlight']['color'] = '#EEABAC'
    return preset

PRESET_EVEN = create_preset(OPTIONS, True)
PRESET_ODD = create_preset(OPTIONS, False)

PRESETS = {
    'Clear': OPTIONS,
    'Even': PRESET_EVEN,
    'Odd': PRESET_ODD
}
