from abc import ABCMeta, abstractmethod

import six

from whylog.log_reader.searchers import BacktrackSearcher


@six.add_metaclass(ABCMeta)
class AbstractLogReader(object):
    @abstractmethod
    def get_causes(self, front_input):
        pass

    @abstractmethod
    def get_causes_tree(self, front_input):
        pass


class LogReader(AbstractLogReader):
    def __init__(self, config):
        self.config = config

    def get_causes(self, front_input):
        input_log_type = self.config.get_log_type(front_input)
        if not input_log_type:
            return None  # TODO information about no input_log_type must somehow be returned to the Front
        investigation_plan = self.config.create_investigation_plan(front_input, input_log_type)
        manager = SearchManager(investigation_plan)
        return manager.investigate()

    def get_causes_tree(self, front_input):
        pass


class SearchManager(object):
    def __init__(self, investigation_plan):
        self._investigation_plan = investigation_plan

    def investigate(self):
        for step, log_type in self._investigation_plan.get_next_investigation_step_with_log_type():
            search_handler = SearchHandler(step, log_type)
            clues = search_handler.investigate()
            # TODO checking up the constraints should take place here
        return InvestigationResult()  # TODO of course return something with sense


class SearchHandler(object):
    def __init__(self, investigation_step, log_type):
        self._investigation_step = investigation_step
        self._log_type = log_type

    def investigate(self):
        clues = {}
        for host, path in self._log_type.get_next_file_to_parse():
            # TODO remember about not localhost case
            searcher = BacktrackSearcher(path)
            clues.update(searcher.search(self._investigation_step))
            # TODO is it a good way to update the dict of clues?
        return clues


class InvestigationResult(object):
    pass  # TODO discuss with Front what should be returned and in what form
    # TODO this class will be probably replaced with FrontInput
