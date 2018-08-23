import unittest
from collections import Sequence

from mock import (
    MagicMock,
    Mock,
    patch,
    sentinel,
)
from unittest_expander import (
    expand,
    foreach,
    param,
)

from rabbit_tools.delete import DelQueueTool
from rabbit_tools.purge import PurgeQueueTool


# these params will be available as class attributes
tested_tools = [
    param(tool=DelQueueTool, do_remove_numbers=True),
    # param(tool=PurgeQueueTool, do_remove_numbers=False),
]


class _ClientMock(Mock):

    sample_get_queues_result = [
        {
            'name': 'queue1',
            'test_attr1': 'sample value 1',
            'test_attr2': 'sample value 2',
        },
        {
            'name': 'queue2',
            'test_attr1': 'sample value 3',
            'test_attr2': 'sample value 4',
        },
        {
            'name': 'queue3',
            'test_attr1': 'sample value 5',
            'test_attr2': 'sample value 6',
        },
        {
            'name': 'queue4',
            'test_attr1': 'sample value 7',
            'test_attr2': 'sample value 8',
        },
    ]

    def __init__(self, *args, **kwargs):
        super(_ClientMock, self).__init__(*args, **kwargs)
        self.output_numbers = {1, 2, 3, 4}
        self.chosen_numbers = set()

    def get_queues(self, *args, **kwargs):
        current_numbers = self.output_numbers - self.chosen_numbers
        return [self.sample_get_queues_result[i-1] for i in current_numbers]

    def delete_queue_nrs(self, numbers):
        """
        Delete one or more queues assigned to selected numbers.

        A helper method, which simulates real deletion of queues
        by the client.

        Args:
            numbers:
                A queue number as integer, list or set of numbers.
        """
        if isinstance(numbers, Sequence):
            numbers = set(numbers)
        elif isinstance(numbers, int):
            numbers = {numbers}
        self.chosen_numbers = self.chosen_numbers | set(numbers)


@expand
@foreach(tested_tools)
class TestRabbitTools(unittest.TestCase):

    sample_mapping = {
        1: 'queue1',
        3: 'queue2',
        6: 'queue3',
        7: 'queue4',
    }

    choose_queues_input_to_expected_output = [
        param(
            user_input='1',
            expected_result={
                1: 'queue1',
            },
        ),
        param(
            user_input='all',
            expected_result=sample_mapping,
        ),
        param(
            user_input='  AlL      ',
            expected_result=sample_mapping,
        ),
        param(
            user_input='0-6',
            expected_result={
                1: 'queue1',
                3: 'queue2',
                6: 'queue3',
            },
        ),
        param(
            user_input='  1  - 128 ',
            expected_result=sample_mapping,
        ),
        param(
            user_input='0, 1,2,7',
            expected_result={
                1: 'queue1',
                7: 'queue4',
            },
        ),
    ]

    choose_queues_wrong_inputs = ['0', '1-2-8', '1-32-', '-123' 'abc', '3a', 'a3']

    parsed_input_to_expected_result = [
        param(
            parsed_input=[1],
            expected_result={
                1: 'queue1',
            },
        ),
        param(
            parsed_input=[1, 3, 8],
            expected_result={
                1: 'queue1',
                3: 'queue2',
            },
        ),
        param(
            parsed_input=[7],
            expected_result={
                7: 'queue4',
            },
        ),
        param(
            parsed_input=[0, 6],
            expected_result={
                6: 'queue3',
            },
        ),
    ]

    parsed_input_to_not_exisiting = [
        [0],
        [],
    ]

    user_input_wrong_to_expected_none = [
        ' 1 ',
        'a1',
        '-1-3',
        '3-8-9',
        '123-',
        '1,,2',
        ',1,2',
        '  12-19   ',
    ]

    logger_patch = patch('rabbit_tools.base.logger')

    def setUp(self):
        self._tested_tool = self.tool.__new__(self.tool)
        self._tested_tool.config = MagicMock()
        self._tested_tool.client = _ClientMock()
        self._tested_tool.do_remove_chosen_numbers = self.do_remove_numbers
        self._tested_tool._parsed_args = Mock()
        self._tested_tool._vhost = sentinel.vhost
        self._tested_tool._method_to_call = Mock()
        self._tested_tool._chosen_numbers = set()

    # def test__aaaget_queue_mapping_first_run(self):
    #     queue_mapping = self._tested_tool._get_queue_mapping()
    #     self.assertIsInstance(queue_mapping, MutableMapping)
    #     self.assertItemsEqual([1, 2, 3, 4], queue_mapping.keys())
    #     self.assertItemsEqual(['queue1', 'queue2', 'queue3', 'queue4'], queue_mapping.values())
    #
    # def test__get_queue_mapping_another_run(self):
    #     chosen_numbers = {1, 3}
    #     self._tested_tool._chosen_numbers = chosen_numbers
    #     if self.do_remove_numbers:
    #         self._tested_tool.client.delete_queue_nrs(chosen_numbers)
    #         expected_numbers = [2, 4]
    #         expected_queues = ['queue2', 'queue4']
    #     else:
    #         expected_numbers = [1, 2, 3, 4]
    #         expected_queues = ['queue1', 'queue2', 'queue3', 'queue4']
    #     queue_mapping = self._tested_tool._get_queue_mapping()
    #     self.assertIsInstance(queue_mapping, MutableMapping)
    #     self.assertItemsEqual(expected_numbers, queue_mapping.keys())
    #     self.assertItemsEqual(expected_queues, queue_mapping.values())

    # @foreach(parsed_input_to_expected_result)
    # def test__get_selected_mapping(self, parsed_input, expected_result):
    #     with self.logger_patch as log_moc:
    #         result = self._tested_tool._get_selected_mapping(self.sample_mapping, parsed_input)
    #         self.assertFalse(log_moc.called)
    #     self.assertEqual(expected_result, result)

    @foreach(parsed_input_to_not_exisiting)
    def test__get_selected_mapping_invalid(self, parsed_input):
        with self.logger_patch as log_moc:
            result = self._tested_tool._get_selected_mapping(self.sample_mapping, parsed_input)
            self.assertTrue(log_moc.called)
            print log_moc

    # @foreach(choose_queues_input_to_expected_output)
    # def test__choose_queues(self, user_input, expected_result):
    #     with patch('__builtin__.raw_input', return_value=user_input),\
    #             self.logger_patch as log_moc:
    #         result = self._tested_tool._get_selected_mapping(self.sample_mapping)
    #         self.assertFalse(log_moc.called)
    #     self.assertIsInstance(result, MutableMapping)
    #     self.assertItemsEqual(expected_result, result)
    #
    # @foreach(choose_queues_wrong_inputs)
    # def test__choose_queues_wrong_inputs(self, first_val):
    #     with patch('__builtin__.raw_input', side_effect=[first_val, '1']),\
    #             self.logger_patch as log_moc:
    #         result = self._tested_tool._get_valid_numbers(self.sample_mapping)
    #         # self.assertTrue(log_moc.error.called)
    #         # log_moc.error.assert_called_with('***')
    #     self.assertIsInstance(result, MutableMapping)
    #     self.assertItemsEqual({1: 'queue1'}, result)
    #
    # @foreach(parsed_input_to_expected_result)
    # def test__parse_input(self, user_input, expected_result):
    #     result = self._tested_tool._parse_input(user_input)
    #     self.assertIsInstance(result, MutableSequence)
    #     self.assertItemsEqual(expected_result, result)
    #
    # @foreach(parsed_input_wrong_to_expected_none)
    # def test__parse_input_wrong_values(self, user_input):
    #     result = self._tested_tool._parse_input(user_input)
    #     self.assertIsNone(result)
    #
    # @foreach(['q', 'Q', 'QUIT', 'quit', 'QuIt', '  eXit    ', ' e', 'E  '])
    # def test_quit_command(self, command):
    #     with patch('__builtin__.raw_input', return_value=command):
    #         result = self._tested_tool._get_valid_numbers(self.sample_mapping)
    #     self.assertIsNone(result)
    #
    # def test_queue_from_args(self):
    #     sample_queue_name = 'some queue'
    #     self._tested_tool._parsed_args.queue_name = sample_queue_name
    #     self._tested_tool.run()
    #     self._tested_tool._method_to_call.assert_called_with(sentinel.vhost, sample_queue_name)
    #
    # def test_queue_chosen_by_user(self):
    #     self._tested_tool._parsed_args.queue_name = None
    #     with patch('__builtin__.raw_input', side_effect=['2', 'q']):
    #         self._tested_tool.run()
    #     self._tested_tool._method_to_call.assert_called_once_with(sentinel.vhost, 'queue2')
    #
    # def test_queue_chosen_by_user_next_choice(self):
    #     self._tested_tool._parsed_args.queue_name = None
    #     self._tested_tool._chosen_numbers = {2}
    #     with patch('__builtin__.raw_input', side_effect=['2', 'q']):
    #         self._tested_tool.run()
    #     self.assertFalse(self._tested_tool._method_to_call.called)
    #

if __name__ == '__main__':
    unittest.main()
