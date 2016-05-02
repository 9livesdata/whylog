class FrontInput(object):
    def __init__(self, offset, line_content, resource_location):
        self.offset = offset
        self.line_content = line_content
        self.resource_location = resource_location

    def __repr__(self):
        return "FrontInput(%s:%s: %s)" % (self.resource_location, self.offset, self.line_content)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
