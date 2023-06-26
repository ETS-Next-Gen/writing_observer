import datetime
import traceback


class DAGExecutionException(Exception):
    '''
    Exception for errors raised during the execution of the dag

    Attributes:
        message -- explanation of the error
    '''

    def __init__(self, error, function, context):
        self.error = error
        self.function = function
        self.context = context

    def to_dict(self):
        # TODO create serialize/deserialize methods for traceback
        return {
            'error': self.error,
            'function': self.function,
            'error_context': self.context,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'traceback': ''.join(traceback.format_tb(self.__traceback__))
        }
