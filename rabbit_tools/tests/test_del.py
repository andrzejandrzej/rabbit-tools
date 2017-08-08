import unittest
from collections import MutableMapping, MutableSequence

from mock import MagicMock, Mock, patch, sentinel
from unittest_expander import expand, foreach, param

from rabbit_tools.delete import DelQueueTool
from rabbit_tools.purge import PurgeQueueTool


tested_tools = [
    param(tool=DelQueueTool, method='delete_queue'),
    param(tool=PurgeQueueTool, method='purge_queue'),
]


@expand
@foreach(tested_tools)
class TestRabbitTools(unittest.TestCase):

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
    ]

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
            user_input='123',
            expected_result=[123],
        ),
        param(
            user_input='12-13',
            expected_result=[12, 13],
        ),
        param(
            user_input='12   -   18',
            expected_result=range(12, 19),
        ),
        param(
            user_input='1, 0,  4,   9,   128',
            expected_result=[0, 1, 4, 9, 128],
        ),
        param(
            user_input='10-3',
            expected_result=[],
        ),
    ]

    parsed_input_wrong_to_expected_none = [
        ' 1 ',
        'a1',
        '-1-3',
        '3-8-9',
        '123-',
        '1,,2',
        ',1,2',
        '  12-19   ',
    ]

    def setUp(self):
        self._tested_tool = self.tool.__new__(self.tool)
        self._tested_tool.config = MagicMock()
        self._tested_tool.client = Mock()
        self._tested_tool.client.get_queues.return_value = self.sample_get_queues_result
        self._tested_tool._parsed_args = Mock()
        self._tested_tool._vhost = sentinel.vhost
        self._tested_tool._method_to_call = Mock()
        self._tested_tool._chosen_numbers = set()

    def test__get_queue_mapping_first_run(self):
        queue_mapping = self._tested_tool._get_queue_mapping()
        self.assertIsInstance(queue_mapping, MutableMapping)
        self.assertItemsEqual([1, 2, 3], queue_mapping.keys())
        self.assertItemsEqual(['queue1', 'queue2', 'queue3'], queue_mapping.values())

    def test__get_queue_mapping_another_run(self):
        self._tested_tool._chosen_numbers = {2, 4}
        queue_mapping = self._tested_tool._get_queue_mapping()
        self.assertIsInstance(queue_mapping, MutableMapping)
        self.assertItemsEqual([1, 3, 5], queue_mapping.keys())
        self.assertItemsEqual(['queue1', 'queue2', 'queue3'], queue_mapping.values())

    @foreach(choose_queues_input_to_expected_output)
    def test__choose_queues(self, user_input, expected_result):
        with patch('__builtin__.raw_input', return_value=user_input):
            result = self._tested_tool._choose_queues(self.sample_mapping)
        self.assertIsInstance(result, MutableMapping)
        self.assertItemsEqual(expected_result, result)

    @foreach(choose_queues_wrong_inputs)
    def test__choose_queues_wrong_inputs(self, first_val):
        with patch('__builtin__.raw_input', side_effect=[first_val, '1']):
            result = self._tested_tool._choose_queues(self.sample_mapping)
        self.assertIsInstance(result, MutableMapping)
        self.assertItemsEqual({1: 'queue1'}, result)

    @foreach(parsed_input_to_expected_result)
    def test__parse_input(self, user_input, expected_result):
        result = self._tested_tool._parse_input(user_input)
        self.assertIsInstance(result, MutableSequence)
        self.assertItemsEqual(expected_result, result)

    @foreach(parsed_input_wrong_to_expected_none)
    def test__parse_input_wrong_values(self, user_input):
        result = self._tested_tool._parse_input(user_input)
        self.assertIsNone(result)

    @foreach(['q', 'Q', 'QUIT', 'quit', 'QuIt', '  eXit    ', ' e', 'E  '])
    def test_quit_command(self, command):
        with patch('__builtin__.raw_input', return_value=command):
            result = self._tested_tool._choose_queues(self.sample_mapping)
        self.assertIsNone(result)

    def test_queue_from_args(self):
        self._tested_tool._parsed_args.queue_name = sentinel.queue
        self._tested_tool.run()
        self._tested_tool._method_to_call.assert_called_with(sentinel.vhost, sentinel.queue)

    def test_queue_chosen_by_user(self):
        self._tested_tool._parsed_args.queue_name = None
        with patch('__builtin__.raw_input', side_effect=['2', 'q']):
            self._tested_tool.run()
        self._tested_tool._method_to_call.assert_called_once_with(sentinel.vhost, 'queue2')

    def test_queue_chosen_by_user_next_choice(self):
        self._tested_tool._parsed_args.queue_name = None
        self._tested_tool._chosen_numbers = {2}
        with patch('__builtin__.raw_input', side_effect=['2', 'q']):
            self._tested_tool.run()
        self.assertFalse(self._tested_tool._method_to_call.called)
