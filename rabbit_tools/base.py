import argparse
import logging
import os
import re
import sys
from collections import Sequence

from pyrabbit import Client
from pyrabbit.http import HTTPError

from rabbit_tools.config import (
    Config,
    ConfigFileMissingException,
)


logger = logging.getLogger(__name__)


class StopReceivingInput(Exception):
    """
    Raised when no queues are left, or user typed a quitting command.
    """


class RabbitToolBase(object):

    config_section = 'rabbit_tools'

    description = NotImplemented
    args = NotImplemented

    client_method_name = NotImplemented

    queue_not_affected_msg = 'Queue not affected'
    queues_affected_msg = 'Queues affected'
    no_queues_affected_msg = 'No queues have been affected.'

    quitting_commands = ['q', 'quit', 'exit', 'e']
    choose_all_commands = ['a', 'all']

    # set to True, if queues are deleted after an action,
    # and the associated number should not be shown anymore
    do_remove_chosen_numbers = False

    single_choice_regex = re.compile(r'^\d+$')
    range_choice_regex = re.compile(r'^(\d+)[ ]*-[ ]*(\d+)$')
    multi_choice_regex = re.compile(r'^(\d+)[ ]*,[ ]*((\d+)[ ]*,[ ]*)*((\d+)[ ]*,?)$')
    multi_choice_inner_regex = re.compile(r'\b(\d+)\b')

    def __init__(self):
        try:
            self.config = Config(self.config_section)
        except ConfigFileMissingException:
            sys.exit('Config file has not been found. Use the "rabbit_tools_config" command'
                     ' to generate it.')
        self._parsed_args = self._get_parsed_args()
        self._vhost = self.config['vhost']
        self.client = self._get_client(**self.config)
        self._method_to_call = getattr(self.client, self.client_method_name)
        self._chosen_numbers = set()

    def _get_parsed_args(self):
        parser = argparse.ArgumentParser(description=self.description)
        for arg_name, arg_opts in self.args.iteritems():
            parser.add_argument(arg_name, **arg_opts)
        return parser.parse_args()

    def _get_client(self, host, port, user, password, **kwargs):
        api_url = self._get_api_url(host, port)
        cl = Client(api_url, user, password)
        return cl

    @staticmethod
    def _get_api_url(host, port):
        return '{0}:{1}'.format(host, str(port))

    def _yield_queue_list(self):
        return (x['name'] for x in self.client.get_queues(self._vhost))

    def _get_queue_mapping(self):
        queue_names = list(self._yield_queue_list())
        if not queue_names:
            raise StopReceivingInput
        full_range = range(1, len(queue_names) + len(self._chosen_numbers) + 1)
        if self.do_remove_chosen_numbers:
            output_range = set(full_range) - self._chosen_numbers
        else:
            output_range = full_range
        return dict(zip(output_range, queue_names))

    @staticmethod
    def _get_user_input(mapping):
        if mapping:
            for nr, queue in mapping.iteritems():
                print '[{}] {}'.format(nr, queue)
            user_input = raw_input("Queue number ('all' to choose all / 'q' to quit'): ")
            user_input = user_input.strip().lower()
            return user_input
        else:
            logger.info('No more queues to choose.')
            raise StopReceivingInput

    def _parse_input(self, user_input):
        if user_input in self.quitting_commands:
            raise StopReceivingInput
        if user_input in self.choose_all_commands:
            return 'all'
        single_choice = self.single_choice_regex.search(user_input)
        if single_choice:
            return [int(single_choice.group(0))]
        range_choice = self.range_choice_regex.search(user_input)
        if range_choice:
            return range(int(range_choice.group(1)), int(range_choice.group(2))+1)
        multi_choice = self.multi_choice_regex.search(user_input)
        if multi_choice:
            raw_numbers = multi_choice.group(0)
            return map(int, self.multi_choice_inner_regex.findall(raw_numbers))
        logger.error('Input could not be parsed.')
        return None

    @staticmethod
    def _validate_numbers(mapping, parsed_input):
        wrong_numbers = [str(x) for x in parsed_input if x not in mapping]
        if wrong_numbers:
            logger.error("Wrong choice: %s.", ', '.join(wrong_numbers))
            return False
        return True

    def _get_chosen_queues_mapping(self, mapping, parsed_input):
        if isinstance(parsed_input, Sequence) and self._validate_numbers(mapping, parsed_input):
            return {nr: mapping[nr] for nr in parsed_input}
        elif parsed_input == 'all':
            return mapping
        return None

    def make_action_from_args(self, all_queues, queue_names):
        if len(queue_names) == 1 and queue_names[0] in self.choose_all_commands:
            chosen_queues = all_queues
        else:
            chosen_queues = queue_names
        affected_queues = []
        for queue in chosen_queues:
            try:
                self._method_to_call(self._vhost, queue)
            except HTTPError as e:
                if e.status == 404:
                    logger.error("Queue %r does not exist.", queue)
                else:
                    logger.warning("%s: %r.", self.queue_not_affected_msg, queue)
            else:
                affected_queues.append(queue)
        else:
            logger.info("%s: %s", self.queues_affected_msg, ', '.join(affected_queues))

    def make_action(self, chosen_queues):
        affected_queues = []
        chosen_numbers = []
        for queue_number, queue_name in chosen_queues.iteritems():
            try:
                self._method_to_call(self._vhost, queue_name)
            except HTTPError as e:
                if e.status == 404:
                    logger.error("Queue %r does not exist.", queue_name)
                    chosen_numbers.append(queue_number)
                else:
                    logger.warning("%s: %r.", self.queue_not_affected_msg, queue_name)
            else:
                affected_queues.append(queue_name)
                chosen_numbers.append(queue_number)
        if affected_queues:
            logger.info("%s: %s.", self.queues_affected_msg, ', '.join(affected_queues))
        else:
            logger.warning(self.no_queues_affected_msg)
        return chosen_numbers

    def run(self):
        queue_names = self._parsed_args.queue_name
        if queue_names:
            all_queues = self._yield_queue_list()
            self.make_action_from_args(all_queues, queue_names)
        else:
            while True:
                try:
                    mapping = self._get_queue_mapping()
                    user_input = self._get_user_input(mapping)
                    parsed_input = self._parse_input(user_input)
                except StopReceivingInput:
                    print 'bye'
                    break
                if parsed_input:
                    chosen_queues_mapping = self._get_chosen_queues_mapping(mapping,
                                                                            parsed_input)
                    if chosen_queues_mapping:
                        self._chosen_numbers.update(self.make_action(chosen_queues_mapping))
