import json
import jsonschema
import os

dir = os.path.dirname(os.path.realpath(__file__))
schema_path = os.path.join(dir, 'schema.json')

with open(schema_path, 'r') as f:
    execution_dag_schema = json.load(f)


def validate_schema(query):
    try:
        jsonschema.validate(query, execution_dag_schema)
        return True
    except jsonschema.ValidationError as e:
        print(e)
        return False
