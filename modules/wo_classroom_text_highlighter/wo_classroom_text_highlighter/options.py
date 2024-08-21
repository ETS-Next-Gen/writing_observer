import copy
import writing_observer

parents = []

OPTIONS = [
    {'id': indicator['id'], 'types': {'highlight': {}, 'metric': {}}, 'label': indicator['name'], 'parent': 'text-information'}
    for indicator in writing_observer.nlp_indicators.INDICATOR_JSONS
]
OPTIONS.append({'id': 'text-information', 'label': 'Text Information', 'parent': ''})


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
