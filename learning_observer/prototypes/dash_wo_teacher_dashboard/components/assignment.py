'''
Used for handling assignment information within the UI
This might not be the best way to handle it.
We'll revisit this piece of the codebase once we hook up assignment information
'''
# package imports
import datetime
import random


class Assignment:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
        self.essay_type = random.choice(['Narrative', 'Argumentative', 'Other'])
        self.start_date = datetime.datetime(2022, 7, 1)
        self.end_date = random.choice([datetime.date(2022, 8, 1), datetime.date(2022, 7, 14), datetime.date(2022, 7, 22)])
        self.active = bool(random.getrandbits(1))
