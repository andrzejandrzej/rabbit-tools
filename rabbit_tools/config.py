import errno
import logging
import os
import sys
from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
)
from ConfigParser import SafeConfigParser

from rabbit_tools.lib import (
    answer_yes_no,
    simple_logger,
    ETC_DIR,
    HOME_DIR,
)


DEFAULT_CONFIG = '''[rabbit_tools]
api_url = 127.0.0.1:15672
user = guest
passwd = guest
vhost = /'''

CONFIG_FILENAME = 'rabbit_tools.conf'


logger = logging.getLogger(__name__)


class ConfigCreator(object):

    description = ('Create a config file for Rabbit Tools to make the tool faster and easier '
                   'to use.')
    rabbit_tools_section = ['host', 'port', 'user', 'password', 'vhost']
    handler_simple = {
        'level': 'NOTSET',
        'class': 'StreamHandler',
        'formatter': 'simple',
        'args': '()',
    }
    handler_syslog = {
        'level': 'NOTSET',
        'class': 'SysLogHandler',
        'args': "('/dev/log',)",
        'formatter': 'full',
    }
    handlers = ['simple']
    formatters = ['full', 'simple']

    def __init__(self):
        self._parsed_args = self._get_parsed_args()
        if not self._parsed_args.no_syslog:
            self.handlers.append('syslog')
        if not len(sys.argv) > 1:
            print "No arguments passed to the script. Use '-h' for help."
            print "Default values will be used."
        self._config = SafeConfigParser()
        self._write_config_sections()

    def _get_parsed_args(self):
        parser = ArgumentParser(description=self.description,
                                formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument('-a', '--host',
                            help='Hostname of RabbitMQ API',
                            default='127.0.0.1')
        parser.add_argument('-p', '--port',
                            help='Port number of RabbitMQ API',
                            default='15672')
        parser.add_argument('-u', '--user', help='Username', default='guest')
        parser.add_argument('-s', '--password', help='Password', default='guest')
        parser.add_argument('-v', '--vhost', help='Vhost', default='/')
        parser.add_argument('--no-syslog', help='Disable logging to syslog', action='store_true')
        parser.add_argument('--stream-log-format',
                            help='Format of stream logs',
                            default='%(levelname)s - %(message)s')
        parser.add_argument('--syslog-log-format',
                            help='Format of syslog logs',
                            default='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return parser.parse_args()

    def _write_config_sections(self):
        self._config.add_section('rabbit_tools')
        for opt in self.rabbit_tools_section:
            self._config.set('rabbit_tools', opt, getattr(self._parsed_args, opt))
        print self._config.items('rabbit_tools')
        self._config.add_section('loggers')
        self._config.add_section('handlers')
        self._config.add_section('formatters')
        self._config.add_section('fff')

    @staticmethod
    def _make_config_file(dir_path):
        config_file = os.path.join(dir_path, CONFIG_FILENAME)
        if os.path.exists(config_file):
            if not answer_yes_no("Config file already exists, do you want to overwrite it?"):
                return True
        try:
            with open(config_file, 'w') as open_config:
                open_config.write(DEFAULT_CONFIG)
        except IOError as e:
            if e.errno == errno.EACCES:
                logger.error("No permission to write to: %r.", config_file)
            elif e.errno == errno.EISDIR:
                logger.error("File %r is a directory!", config_file)
            else:
                logger.exception("Cannot write config file to: %r.", config_file)
            return False
        except Exception:
            logger.error("Cannot write config file to: %r.", config_file)
            return False
        logger.info('Config file was successfully written to: %r.', config_file)
        return True

    @staticmethod
    def _make_dir(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                return True
            elif e.errno == errno.EACCES:
                logger.error("No permission to write to: %r.", dir_path)
                return False
            else:
                return False
        return True

    def create_config_file(self):
        if answer_yes_no("Do you want to write a new config file?"):
            if not self._make_dir(ETC_DIR) or not self._make_config_file(ETC_DIR):
                logger.info("Could not write config file to: %r, using: %r.", ETC_DIR, HOME_DIR)
                if not self._make_dir(HOME_DIR) or not self._make_config_file(HOME_DIR):
                    sys.exit("Failed to write a config file.")


def main():
    with simple_logger():
        config_creator = ConfigCreator()
        config_creator.create_config_file()


if __name__ == '__main__':
    main()
