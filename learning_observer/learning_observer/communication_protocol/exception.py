import datetime
import traceback


class DAGExecutionException(Exception):
    '''
    Exception for errors raised during the execution of the dag

    Attributes:
        function -- the function causing the error
        error_provenance -- any items that may be useful for debugging the error
        timestamp -- when the error occured
        traceback -- traceback object for error
    '''

    def __init__(self, error, function, provenance):
        self.error = error
        self.function = function
        self.provenance = provenance

    def to_dict(self):
        # TODO create serialize/deserialize methods for traceback
        return {
            'error': self.error,
            'function': self.function,
            'error_provenance': self.provenance,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'traceback': ''.join(traceback.format_tb(self.__traceback__))
        }
