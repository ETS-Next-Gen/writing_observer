import anthropic
import dotenv
import json
import os
import re

dotenv.load_dotenv()

API_KEY = os.environ['ANTHROPIC_API_KEY']
MODEL_NAME = 'claude-3-5-sonnet-20241022'


def replace_variables_in_string(string=None, variables=None):
    if variables is None:
        variables = {}

    replaced = re.sub(r'\{\{(.*?)\}\}', lambda match: str(variables.get(match.group(1), '')), string)
    return replaced


def create_llm_messager(tools=None, system_template=None, messages_template=None):
    if tools is None:
        tools = []
    if system_template is None:
        system_template = 'You are a useful agent'
    if messages_template is None:
        messages_template = [{'role': 'user', 'content': '{query}'}]
    client = anthropic.Anthropic(api_key=API_KEY)

    tool_implementations = {tool['name']: tool['function'] for tool in tools}
    tool_schemas = [{k: v for k, v in tool.items() if k != 'function'} for tool in tools]

    def process_query(variables=None):
        system = replace_variables_in_string(system_template)
        messages = []
        for m in messages_template:
            m['content'] = replace_variables_in_string(str(m['content']), variables)
            messages.append(m)

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=8192,
            temperature=0.7,
            tools=tool_schemas,
            system=system,
            messages=messages
        )

        while response.stop_reason == 'tool_use':
            tool_use = next(block for block in response.content if block.type == 'tool_use')
            tool_fn = tool_implementations.get(tool_use.name)
            if tool_fn:
                try:
                    result = tool_fn(**tool_use.input)
                except Exception as e:
                    result = json.dumps({'error': str(e)})
            else:
                result = json.dumps({'error': 'Tool not found'})

            messages.extend([
                {'role': 'assistant', 'content': response.content},
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'tool_result',
                            'tool_use_id': tool_use.id,
                            'content': str(result),
                        }
                    ],
                }
            ])

            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=4096,
                tools=tool_schemas,
                messages=messages
            )

        final_response = next(
            (block.text for block in response.content if hasattr(block, 'text')),
            None,
        )
        messages.append({'role': 'assistant', 'content': final_response})
        # TODO return messages
        return final_response
    
    return process_query



# Toy tool examples
def get_current_weather(location: str, unit: str = 'celsius'):
    print('*** Grabbing the current weather')
    return json.dumps({'temperature': '22', 'unit': unit, 'location': location})


def currency_converter(amount: float, from_currency: str, to_currency: str):
    print('*** Converting the currency')
    rates = {'USD': {'EUR': 0.93}, 'EUR': {'USD': 1.07}}
    return json.dumps({'converted': amount * rates[from_currency][to_currency]})


# Toy tool example that calls an agent
def restaurant_booking(datetime: str, party_size: int, cuisine: str = ""):
    """Nested agent for handling restaurant reservations"""
    print('\n*** Starting restaurant booking sub-agent')
    
    # Create specialized booking agent
    booking_agent = create_llm_messager(
        tools=[],  # This agent doesn't need tools
        system_template=(
            'You are an upscale restaurant booking assistant. '
            'Confirm bookings with creative descriptions. '
            'Always include an emoji matching the cuisine type.'
        ),
        messages_template=[
            {
                'role': 'user',
                'content': (
                    'Create a restaurant booking confirmation for:\n'
                    'Date/Time: {{datetime}}\n'
                    'Party Size: {{party_size}}\n'
                    'Cuisine Type: {{cuisine}}\n\n'
                    'Include a confirmation number.'
                )
            }
        ]
    )
    
    # Call sub-agent with formatted parameters
    booking_confirmation = booking_agent(variables={
        'datetime': datetime,
        'party_size': party_size,
        'cuisine': cuisine or 'any'
    })
    
    return json.dumps({
        'confirmation': booking_confirmation,
        'details': {
            'datetime': datetime,
            'party_size': party_size,
            'cuisine': cuisine
        }
    })


# Tool schemas
tools = [
    {
        'name': 'get_current_weather',
        'description': 'Get current weather information',
        'input_schema': {
            'type': 'object',
            'properties': {
                'location': {'type': 'string', 'description': 'City and country'},
                'unit': {'type': 'string', 'enum': ['celsius', 'fahrenheit']}
            },
            'required': ['location']
        },
        'function': get_current_weather
    },
    {
        'name': 'currency_converter',
        'description': 'Convert between currencies',
        'input_schema': {
            'type': 'object',
            'properties': {
                'amount': {'type': 'number'},
                'from_currency': {'type': 'string', 'enum': ['USD', 'EUR', 'GBP']},
                'to_currency': {'type': 'string', 'enum': ['USD', 'EUR', 'GBP']}
            },
            'required': ['amount', 'from_currency', 'to_currency']
        },
        'function': currency_converter
    },{
        'name': 'restaurant_booking',
        'description': 'Book a restaurant table',
        'input_schema': {
            'type': 'object',
            'properties': {
                'datetime': {'type': 'string', 'description': 'ISO 8601 datetime'},
                'party_size': {'type': 'integer'},
                'cuisine': {'type': 'string', 'description': 'Preferred cuisine type'}
            },
            'required': ['datetime', 'party_size']
        },
        'function': restaurant_booking
    }
]


agent = create_llm_messager(
    tools=tools,
    messages_template=[
        {'role': 'user', 'content': 'Answer in English. Please help me with: {{query}}'}
    ]
)

# Example usage
response = agent(variables={
    'query': "What's the weather in Paris and how much is 100 USD in EUR?"
})
