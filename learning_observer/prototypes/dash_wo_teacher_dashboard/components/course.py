# package imports
from faker import Faker
import json
import os

# local imports
from .assignment import Assignment

fake = Faker()

cwd = os.getcwd()
data_in = os.path.join(cwd, 'data', 'set_2_data.json')
with open(data_in, 'r') as f:
    assignment = json.load(f)

class Course:
    def __init__(self, id, role):
        self.id = id
        self.name = f'Course {id}'
        self.role = role

        if role == 'teacher':
            self.students = self.fetch_students()
            self.assignments = [Assignment(0, assignment['name'], assignment['description'])]
        elif role == 'student':
            self.dashboard = 'BRUH'
        else:
            self.dashboard = 'No role'

    def fetch_students(self):
        return [
            {
                'id': i,
                'name': fake.name()
            } for i in range(24)
        ]
