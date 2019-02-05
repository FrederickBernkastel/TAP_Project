"""API Error formats
"""


class InvalidUsage(Exception):
    """Error format for invalid usage of API
    
    Error format for invalid usage of API. Holds information about the error,
    and contains helper functions to convert this information into a dictionary
    for JSON
    """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        """Initializes exception with message about error
        
        Parameters
        ----------
        message: string
            Information about error
        status_code: int
            HTTP status code
        payload: dic
            Additional information about error to be included in error JSON
        
        """
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Converts contained error information into dictionary
        
        Returns
        -------
        dict:
            dictionary containing error information
        """
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv
    
    