import datetime
import traceback


class DAGExecutionException(Exception):
    '''
    Exception for errors raised during the execution of the dag

    Attributes:
        message -- explanation of the error
    '''

    def __init__(self, error, function, providence):
        self.error = error
        self.function = function
        self.providence = providence

    def to_dict(self):
        # TODO create serialize/deserialize methods for traceback
        return {
            'error': self.error,
            'function': self.function,
            'error_providence': self.providence,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'traceback': ''.join(traceback.format_tb(self.__traceback__))
        }
