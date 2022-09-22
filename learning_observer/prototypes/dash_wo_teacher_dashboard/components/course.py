'''
Handle Course information in the UI
Currently prepopulates the course with a single assignment from the dataset
'''

# package imports
from faker import Faker
import json
import os

# local imports
from .assignment import Assignment

fake = Faker()

cwd = os.getcwd()
data_in = os.path.join(cwd, 'uncommitted', 'set_2_data.json')
with open(data_in, 'r') as f:
    assignment = json.load(f)


class Course:
    def __init__(self, id):
        self.id = id
        self.name = f'Course {id}'

        self.students = self.fetch_students()
        self.assignments = [Assignment(0, assignment['name'], assignment['description'])]

    def fetch_students(self):
        return [
            {
                'id': i,
                'name': fake.name()
            } for i in range(24)
        ]
