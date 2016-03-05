from unittest import TestCase
import os.path

from whylog.tests.tests_client.constants import TestPaths, AFewLinesLogParams
from whylog.client import searchers


class TestBacktrackSearcher(TestCase):
    def _count_lines_in_file(self, file_path):
        return sum(1 for line in open(file_path))

    def _get_sample_offset(self, line_num):
        """
        Returns the correct offset of line 'line_num'
        referring to the file a_few_lines.log construction.
        Be careful when modifying a_few_lines.log.
        """
        assert line_num <= self._count_lines_in_file(
            TestPaths.get_file_path(
                AFewLinesLogParams.FILE_NAME
            )
        )
        return line_num * AFewLinesLogParams.SINGLE_LINE_LENGTH

    def _read_all_lines_from_file(self, file_path):
        with open(file_path) as f:
            return f.read().splitlines()

    def _read_last_n_lines_from_file(self, file_path, how_many_lines):
        with open(file_path) as f:
            return f.read().splitlines()[:how_many_lines]

    def _verify_lines(self, lines_normally, lines_reversed):
        assert len(lines_reversed) == len(lines_normally)
        for i, j in zip(lines_reversed, reversed(lines_normally)):
            assert i == j

    def _run_reverse_and_check_results(
        self, log_file_path, reverse_from_offset_params, how_many_last_lines
    ):
        backtracker = searchers.BacktrackSearcher(log_file_path)

        lines = self._read_last_n_lines_from_file(log_file_path, how_many_last_lines)
        lines_reversed = list(backtracker._reverse_from_offset(*reverse_from_offset_params))

        self._verify_lines(lines_reversed, lines)

    def _sample_call_with_specified_bufsize(self, bufsize):
        log_file_path = TestPaths.get_file_path(AFewLinesLogParams.FILE_NAME)
        how_many_lines = 7
        offset = self._get_sample_offset(how_many_lines)
        self._run_reverse_and_check_results(log_file_path, [offset, bufsize], how_many_lines)

    def test_very_small_bufsize(self):
        for i in range(1, 3):
            self._sample_call_with_specified_bufsize(i)

    def test_file_size_as_offset(self):
        log_file_path = TestPaths.get_file_path(AFewLinesLogParams.FILE_NAME)
        file_size_as_offset = os.path.getsize(log_file_path)
        self._run_reverse_and_check_results(
            log_file_path, [file_size_as_offset], self._count_lines_in_file(log_file_path)
        )
