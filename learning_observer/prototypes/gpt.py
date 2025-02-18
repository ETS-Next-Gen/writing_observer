#!/home/pmitros/.virtualenvs/hugging/bin/python

# You might need something like:
#activate_this = "[]/.virtualenvs/[]/bin/activate_this.py"
#exec(open(activate_this).read(), dict(__file__=activate_this))

from datetime import datetime
import argparse
import json
import os
import os.path
import subprocess
import sys
import tempfile


try:
    from openai import OpenAI
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = open(os.path.join(os.path.expanduser("~"), ".ssh", "openai-key")).read().strip()
    openai_available = True
except:
    openai_available = False

try:
    from groq import Groq
    if "GROQ_API_KEY" not in os.environ:
        os.environ["GROQ_API_KEY"] = open(os.path.join(os.path.expanduser("~"), ".ssh", "groq-key")).read().strip()
    groq_available = True
except ImportError:
    groq_available = False

try:
    from anthropic import Anthropic
    if "ANTHROPIC_API_KEY" not in os.environ:
        os.environ["ANTHROPIC_API_KEY"] = open(os.path.join(os.path.expanduser("~"), ".ssh", "anthropic-key")).read().strip()
    anthropic_available = True
except ImportError:
    anthropic_available = False


def parse_arguments():
    parser = argparse.ArgumentParser(description="Interactive AI chat client.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Enable interactive mode.")
    parser.add_argument("--load-prompt", type=str, help="Path to a system prompt file to load.")
    parser.add_argument("--load-conversation", type=str, help="Path to a previous conversation log to load.")
    parser.add_argument("--save-log", type=str, help="Path to save the final conversation log.", default=None)
    parser.add_argument("-m", "--model", type=str, help="Specify the model to use (overrides default).")
    parser.add_argument("--temperature", type=float, default=0.7, help="Set the sampling temperature (default: 0.7).")
    parser.add_argument("question", nargs="?", type=str, help="Single question for non-interactive mode.")
    return parser.parse_args()

def exit_handler():
    print("Exiting conversation.")
    raise EOFError()

def load_conversation(filename):
    with open(filename, 'r') as file:
        return json.load(file)

def load_handler(conversation, filename):
    if filename and os.path.exists(filename):
        loaded_conversation = load_conversation(filename)
        conversation.clear()
        conversation.extend(loaded_conversation)
        print(f"Loaded conversation from {filename}.")
    else:
        print("File not found or no filename provided.")

def save_handler(conversation, filename):
    filename = save_chat_log(conversation, filename)
    print(f"Chat log saved to {filename}.")

def save_chat_log(conversation, filename=None):
    if filename is None:
        with tempfile.NamedTemporaryFile(delete=False, prefix="chat_log_", suffix=".json", dir="/tmp") as temp_file:
            filename = temp_file.name
    with open(filename, 'w') as file:
        json.dump(conversation, file, indent=2)
    return filename

def edit_handler(conversation):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        filename = temp_file.name
        with open(filename, 'w') as file:
            json.dump(conversation, file, indent=2)
    editor = os.getenv('EDITOR', 'nano')

    while True:
        try:
            subprocess.call([editor, filename])
            with open(filename, 'r') as file:
                edited_conversation = json.load(file)
            break
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}. You can either fix it in the editor or revert to the previous state.")
            if input("Revert? (y/n): ").strip().lower() == 'y':
                print("Reverting to the previous state.")
                return

    conversation.clear()
    conversation.extend(edited_conversation)

def get_model(model_name):
    """
    Determine which client and model to use based on the script name or model name
    """
    print('Initiallizing system with model name:', model_name)
    # OpenAI models (default fallback)
    if model_name.startswith('gpt'):
        if not openai_available:
            raise ValueError("OpenAI client not installed. Please install `openai` package.")
        return {
            'provider': 'openai',
            'client': OpenAI(),
            'model': model_name if model_name != 'gpt' else 'gpt-4o-mini',
            'method': 'openai'
        }
    
    # Groq models
    if model_name.startswith('groq'):
        if not groq_available:
            raise ValueError("Groq client not installed. Please install `groq` package.")
        groq_model = model_name.replace('groq-', '')
        if groq_model == 'groq':
            groq_model = 'llama-3.3-70b-versatile'
        return {
            'provider': 'groq',
            'client': Groq(api_key=os.environ.get("GROQ_API_KEY")),
            'model': groq_model,
            'method': 'groq'
        }
    
    # Claude/Anthropic models
    if model_name.startswith('claude'):
        if not anthropic_available:
            raise ValueError("Anthropic client not installed. Please install `anthropic` package.")

        # Default to Claude 3 Haiku if no specific version specified
        if model_name == 'claude':
            model_name = 'claude-3-5-sonnet-latest'

        return {
            'provider': 'anthropic',
            'client': Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")),
            'model': model_name,
            'method': 'anthropic'
        }
    
    raise ValueError(f"Unsupported model: {model_name}")

def read_multiline_input(model):
    print(model)
    lines = []
    while True:
        try:
            line = input()
            lines.append(line)
        except EOFError:
            break
    return '\n'.join(lines)



def _generate_openai_groq_response(conversation, config):
    tool_implementations = {tool['function']['name']: tool['function_call'] for tool in config['tools']}
    tool_schemas = [{k: v for k, v in tool.items() if k != 'function_call'} for tool in config['tools']]

    if config['system_prompt'] is not None:
        conversation.insert(0, {"role": "developer", "content": config['system_prompt']})
    response = config['client'].chat.completions.create(
        model=config['model'],
        tools=tool_schemas,
        messages=conversation,
        temperature=config['temperature']
    )
    response_message = response.choices[0].message.content
    conversation.append(response.choices[0].message.to_dict())

    tool_calls = response.choices[0].message.tool_calls
    for tool_call in tool_calls if tool_calls else []:
        # If true the model will return the name of the tool / function to call and the argument(s)
        tool_call_id = tool_call.id
        tool_fn = tool_implementations[tool_call.function.name]
        tool_query_string = json.loads(tool_call.function.arguments)

        if tool_fn:
            try:
                result = tool_fn(**tool_query_string)
            except Exception as e:
                result = json.dumps({'error': str(e)})
        else:
            result = json.dumps({'error': 'Tool not found'})

        conversation.append({
            'role': 'tool',
            'tool_call_id': tool_call_id,
            'name': tool_call.function.name,
            'content': result
        })

    # get a final response after tool calls are made
    if tool_calls:
        response = config['client'].chat.completions.create(
            model=config['model'],
            tools=tool_schemas,
            messages=conversation,
            temperature=config['temperature']
        )
        response_message = response.choices[0].message.content
        conversation.append({'role': 'assistant', 'content': response_message})

    return response_message


def _generate_anthropic_response(conversation, config):
    tool_implementations = {tool['name']: tool['function'] for tool in config['tools']}
    tool_schemas = [{k: v for k, v in tool.items() if k != 'function'} for tool in config['tools']]

    response = config['client'].messages.create(
        model=config['model'],
        max_tokens=4096,
        messages=conversation,
        tools=tool_schemas,
        temperature=config['temperature'],
        **({'system': config['system_prompt']} if config['system_prompt'] is not None else {})
    )
    conversation.append({'role': 'assistant', 'content': response.to_dict()['content']})
    tool_results = []
    for tool_use in response.content:
        if tool_use.type != 'tool_use':
            continue
        tool_fn = tool_implementations.get(tool_use.name)
        if tool_fn:
            try:
                result = tool_fn(**tool_use.input)
            except Exception as e:
                result = json.dumps({'error': str(e)})
        else:
            result = json.dumps({'error': 'Tool not found'})

        tool_results.append({
            'type': 'tool_result',
            'tool_use_id': tool_use.id,
            'content': str(result),
        })

    if len(tool_results) > 0:
        conversation.append({
            'role': 'user',
            'content': tool_results
        })

        response = config['client'].messages.create(
            model=config['model'],
            max_tokens=4096,
            messages=conversation,
            tools=tool_schemas,
            temperature=config['temperature'],
            **({'system': config['system_prompt']} if config['system_prompt'] is not None else {})
        )

        conversation.append({'role': 'assistant', 'content': response.to_dict()['content']})
    return response.content[0].text


RESPONSE_GENERATORS = {
    'openai': _generate_openai_groq_response,
    'groq': _generate_openai_groq_response,
    'anthropic': _generate_anthropic_response
}

def generate_response(conversation, config):
    if config['method'] in ['openai', 'groq']:
        system_messages = []
        if config['system_prompt'] is not None:
            system_messages.append({"role": "developer", "content": config['system_prompt']})
        completion = config['client'].chat.completions.create(
            model=config['model'],
            messages=system_messages + conversation,
            temperature=config['temperature']
       )
        return completion.choices[0].message.content
    else:
        completion = config['client'].messages.create(
            model=config['model'],
            max_tokens=4096,
            messages=conversation,
            temperature=config['temperature'],
            **({'system': config['system_prompt']} if config['system_prompt'] is not None else {})
        )
        return completion.content[0].text


def generate_response_new(conversation, config):
    print('Starting to generate a response')
    return RESPONSE_GENERATORS[config['method']](conversation, config)


# def interactive_mode(config, conversation):
#     handlers = {
#         'exit': lambda args: exit_handler(),
#         'save': lambda args: save_handler(conversation, args),
#         'load': lambda args: load_handler(conversation, args),
#         'edit': lambda args: edit_handler(conversation)
#     }
#     print(f"{config['model']}: Start asking questions or use commands (e.g., \\exit, \\save [filename], \\load [filename], \\edit).")
#     while True:
#         try:
#             question = read_multiline_input(config['model'])
#         except KeyboardInterrupt:
#             break
#         print("-")
#         if question.startswith('\\'):
#             command, *args = question[1:].split(' ', 1)
#             args = args[0].strip() if args and args[0].strip() else None
#             if command in handlers:
#                 try:
#                     handlers[command](args)
#                 except EOFError:
#                     break
#             else:
#                 print(f"Unknown command: \\{command}")
#             continue

#         conversation.append({"role": "user", "content": question})
#         response = generate_response(conversation, config)
#         print(response)
#         conversation.append({"role": "assistant", "content": response})

#     return conversation
def interactive_mode(config, conversation):
    handlers = {
        'exit': lambda args: exit_handler(),
        'save': lambda args: save_handler(conversation, args),
        'load': lambda args: load_handler(conversation, args),
        'edit': lambda args: edit_handler(conversation)
    }
    print(f"{config['model']}: Start asking questions or use commands (e.g., \\exit, \\save [filename], \\load [filename], \\edit).")
    
    while True:
        try:
            # Determine who should act next based on the last speaker
            if not conversation or conversation[-1]['role'] == 'assistant':
                # It's the user's turn to speak
                question = read_multiline_input(config['model'])
                print("-")
                if question.startswith('\\'):
                    # Handle special commands
                    command, *args = question[1:].split(' ', 1)
                    args = args[0].strip() if args and args[0].strip() else None
                    if command in handlers:
                        try:
                            handlers[command](args)
                        except EOFError:
                            break
                    else:
                        print(f"Unknown command: \\{command}")
                    continue
                
                # Add user's input to the conversation
                conversation.append({"role": "user", "content": question})
            else:
                # It's the assistant's turn to respond
                response = generate_response(conversation, config)
                print(response)
                conversation.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            break

    return conversation


# Toy tool examples
def get_current_weather(location: str, unit: str = 'celsius'):
    print('*** Grabbing the current weather')
    return json.dumps({'temperature': '22', 'unit': unit, 'location': location})


def currency_converter(amount: float, from_currency: str, to_currency: str):
    print('*** Converting the currency')
    rates = {'USD': {'EUR': 0.93}, 'EUR': {'USD': 1.07}}
    return json.dumps({'converted': amount * rates[from_currency][to_currency]})


anthropic_tools = [
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
                'from_currency': {'type': 'string', 'enum': ['USD', 'EUR']},
                'to_currency': {'type': 'string', 'enum': ['USD', 'EUR']}
            },
            'required': ['amount', 'from_currency', 'to_currency']
        },
        'function': currency_converter
    }
]


opeanai_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit to use. Infer this from the users location.",
                    },
                },
                "required": ["location", "unit"],
            },
        },
        'function_call': get_current_weather
    },
    {
        "type": "function",
        "function": {
            "name": "currency_converter",
            "description": "Convert currency from USD to EUR or from EUR to USD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "enum": ['USD', 'EUR'],
                        "description": "The currency to convert from.",
                    },
                    "to_currency": {
                        "type": "string",
                        "enum": ['USD', 'EUR'],
                        "description": "The currency to convert to",
                    },
                    "amount": {
                        "type": "float",
                        "description": "The amount of currency to convert",
                    }
                },
                "required": ["amount", "from_currency", "to_currency"]
            },
        },
        'function_call': currency_converter
    },
]


def main():
    args = parse_arguments()
    if args.model:
        config = get_model(args.model)
    else:
        config = get_model(os.path.basename(sys.argv[0]))

    config['temperature'] = args.temperature if hasattr(args, 'temperature') else 0.7

    if args.load_prompt:
        with open(args.load_prompt, 'r') as file:
            config['system_prompt'] = file.read()
            print(f"Loaded system prompt from {args.load_prompt}.")
    else:
        config['system_prompt'] = None

    if args.load_conversation:
        conversation = load_conversation(args.load_conversation)
        print(f"Loaded conversation from {args.load_conversation}.")
    else:
        conversation = []

    # TODO
    config['tools'] = anthropic_tools if 'claude' in args.model else opeanai_tools

    if args.question and args.interactive:
        print("Either interactive mode or a question. Not both!")
        sys.exit(-1)
    elif not args.interactive:
        if args.question:
            conversation.append({"role": "user", "content": args.question})
        else:
            conversation.append({"role": "user", "content": read_multiline_input(config['model'])})
            response = generate_response_new(conversation, config)
            print(response)
            # conversation.append({"role": "assistant", "content": response})
    else:
        interactive_mode(config, conversation)

    if args and args.save_log:
        log_filename = save_chat_log(conversation, args.save_log)
    else:
        log_filename = save_chat_log(conversation)

    print(f"Chat log saved to {log_filename}")


if __name__ == '__main__':
    main()
