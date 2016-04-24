from abc import ABCMeta, abstractmethod
import dateutil.parser

import six


@six.add_metaclass(ABCMeta)
class AbstractConverter(object):
    @classmethod
    @abstractmethod
    def convert(cls, pattern_group):
        pass


class IntConverter(AbstractConverter):
    @classmethod
    @abstractmethod
    def convert(cls, pattern_group):
        return int(pattern_group)


# Simple date convertion replace for concreate
class DateConverter(AbstractConverter):
    @classmethod
    @abstractmethod
    def convert(cls, pattern_group):
        return dateutil.parser.parse(pattern_group, fuzzy=True)
