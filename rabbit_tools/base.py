import argparse
import logging
import os
import re
import sys
from ConfigParser import (
    NoSectionError,
    SafeConfigParser,
)

from pyrabbit import Client
from pyrabbit.http import HTTPError


logger = logging.getLogger(__name__)


class RabbitToolBase(object):

    config_section = 'rabbit_tools'
    config_dirs = [
        '/etc/rabbit_tools/rabbit_tools.conf',
        os.path.expanduser('~/.rabbit_tools/rabbit_tools.conf'),
    ]

    description = NotImplemented
    args = NotImplemented

    client_method_name = NotImplemented

    queue_not_affected_msg = 'Queue not affected'
    queues_affected_msg = 'Queues affected'
    no_queues_affected_msg = 'No queues have been affected.'

    quitting_commands = ['q', 'quit', 'exit', 'e']
    choose_all_commands = ['a', 'all']

    single_choice_regex = re.compile(r'^\d+$')
    range_choice_regex = re.compile(r'^(\d+)[ ]*-[ ]*(\d+)$')
    multi_choice_regex = re.compile(r'^(\d+)[ ]*,[ ]*((\d+)[ ]*,[ ]*)*((\d+)[ ]*,?)$')
    multi_choice_inner_regex = re.compile(r'\b(\d+)\b')

    def __init__(self):
        self.config = self._get_config()
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

    def _get_config(self):
        config_parser = SafeConfigParser()
        for config_dir in self.config_dirs:
            config_parser.read(config_dir)
            try:
                config_items = config_parser.items(self.config_section)
            except NoSectionError:
                pass
            else:
                return {opt: val for opt, val in config_items}
        sys.exit('Config file has not been found. Use the "rabbit_tools_config" command'
                 ' to generate it.'.format(self.config_dirs[0], self.config_dirs[1]))

    def _get_client(self, host, port, user, password, **kwargs):
        api_url = self._get_api_url(host, port)
        cl = Client(api_url, user, password)
        return cl

    @staticmethod
    def _get_api_url(host, port):
        return '{0}:{1}'.format(host, str(port))

    def _get_queue_mapping(self):
        queue_names = [x['name'] for x in self.client.get_queues(self._vhost)]
        full_range = range(1, len(queue_names) + len(self._chosen_numbers) + 1)
        cleared_range = set(full_range) - self._chosen_numbers
        return dict(zip(cleared_range, queue_names))

    def _choose_queues(self, mapping):
        while mapping:
            for nr, queue in mapping.iteritems():
                print '[{}] {}'.format(nr, queue)
            user_input = raw_input("Queue number ('all' to choose all / 'q' to quit'): ")
            user_input = user_input.strip().lower()
            if user_input in self.quitting_commands:
                return None
            if user_input in self.choose_all_commands:
                return mapping
            parsed_input = self._parse_input(user_input)
            if parsed_input:
                wrong_numbers = [str(x) for x in parsed_input if x not in mapping]
                if wrong_numbers:
                    logger.error("Wrong choice: %s.", ', '.join(wrong_numbers))
                    continue
                result = {nr: mapping[nr] for nr in parsed_input if nr in mapping}
                if result:
                    return result
            else:
                logger.error('Input could not be parsed.')
        else:
            logger.info('No more queues to choose.')
            return None

    def _parse_input(self, user_input):
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
        return None

    def _get_users_choice(self):
            numbers_to_queue_names = self._get_queue_mapping()
            chosen_queues = self._choose_queues(numbers_to_queue_names)
            if chosen_queues is None:
                return None
            return chosen_queues

    def make_single_action(self, queue_name):
        if queue_name.lower() == 'all':
            all_queues = self._get_queue_mapping().values()
            for queue in all_queues:
                try:
                    self._method_to_call(self._vhost, queue)
                except HTTPError:
                    logger.error("Queue not affected due to HTTP Error: %r.", queue)
                else:
                    logger.info("%s: %r.", self.queues_affected_msg, queue_name)
        else:
            try:
                self._method_to_call(self._vhost, queue_name)
            except HTTPError as e:
                if e.status == 404:
                    logger.error("Queue %r does not exist.", queue_name)
                else:
                    logger.error("%s: %r.", self.queue_not_affected_msg, queue_name)
            else:
                logger.info("%s: %r.", self.queues_affected_msg, queue_name)

    def pick_and_make_action(self, chosen_queues):
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
                    logger.info("%s: %r.", self.queue_not_affected_msg, queue_name)
            else:
                affected_queues.append(queue_name)
                chosen_numbers.append(queue_number)
        if affected_queues:
            logger.info("%s: %s.", self.queues_affected_msg, ', '.join(affected_queues))
        else:
            logger.warning(self.no_queues_affected_msg)
        return chosen_numbers

    def run(self):
        queue_name = self._parsed_args.queue_name
        if queue_name:
            self.make_single_action(queue_name)
        else:
            chosen_queues = {}
            while chosen_queues is not None:
                chosen_queues = self._get_users_choice()
                if chosen_queues:
                    self._chosen_numbers.update(self.pick_and_make_action(chosen_queues))
            else:
                print 'bye'
