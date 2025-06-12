class ToolError(Exception):
    """Raised when a tool encounters an error."""

    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message
