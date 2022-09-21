# package imports
from dash import html
import dash_bootstrap_components as dbc
import datetime
import platform
import random

date_format = '%B %#d, %G' if platform.system() == 'Windows' else '%B %-d, %G'
# as long as we don't have callbacks involve the
# functions could easily be turned into class methods
class Assignment:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
        self.essay_type = random.choice(['Narrative', 'Argumentative', 'Other'])
        self.start_date = datetime.datetime(2022, 7, 1)
        self.end_date = random.choice([datetime.date(2022, 8, 1), datetime.date(2022, 7, 14), datetime.date(2022, 7, 22)])
        self.active = bool(random.getrandbits(1))
