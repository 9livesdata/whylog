class NoDateGroupError(Exception):
    def __init__(self, line_content, regex, line_index):
        self.line_content = line_content
        self.regex = regex
        self.line_index = line_index

    def __str__(self):
        return 'No date group in regex. Regex: %s. Line content: %s' % (
            self.regex, self.line_content
        )
