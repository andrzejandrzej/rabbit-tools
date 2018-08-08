import errno
import logging
import os
import sys
from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
)
from ConfigParser import (
    NoSectionError,
    SafeConfigParser,
)

from rabbit_tools.lib import (
    answer_yes_no,
    simple_logger,
    ETC_DIR,
    HOME_DIR,
)


CONFIG_FILENAME = 'rabbit_tools.conf'
logger = logging.getLogger(__name__)


class ConfigFileMissingException(Exception):
    """Raised when no config file was found."""


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
        joined_handlers = ','.join(self.handlers)
        joined_formatters = ','.join(self.formatters)
        self._write_loggers(joined_handlers)
        self._write_handlers(joined_handlers)
        self._write_formatters(joined_formatters)

    def _write_loggers(self, handlers):
        self._config.add_section('loggers')
        self._config.set('loggers', 'keys', 'root')
        self._config.add_section('logger_root')
        self._config.set('logger_root', 'level', 'INFO')
        self._config.set('logger_root', 'handlers', handlers)

    def _write_handlers(self, handlers):
        self._config.add_section('handlers')
        self._config.set('handlers', 'keys', handlers)
        self._config.add_section('handler_simple')
        self._config.set('handler_simple', 'level', 'NOTSET')
        self._config.set('handler_simple', 'class', 'StreamHandler')
        self._config.set('handler_simple', 'formatter', 'simple')
        self._config.set('handler_simple', 'args', '()')
        self._config.add_section('handler_syslog')
        self._config.set('handler_syslog', 'level', 'NOTSET')
        self._config.set('handler_syslog', 'class', 'logging.handlers.SysLogHandler')
        self._config.set('handler_syslog', 'formatter', 'full')
        self._config.set('handler_syslog', 'args', "('/dev/log',)")

    def _write_formatters(self, formatters):
        self._config.add_section('formatters')
        self._config.set('formatters', 'keys', formatters)
        self._config.add_section('formatter_full')
        self._config.set('formatter_full', 'format',
                         '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self._config.add_section('formatter_simple')
        self._config.set('formatter_simple', 'format', '%(levelname)s - %(message)s')

    def _make_config_file(self, dir_path):
        config_file = os.path.join(dir_path, CONFIG_FILENAME)
        if os.path.exists(config_file):
            if not answer_yes_no("Config file already exists, do you want to overwrite it?"):
                return True
        try:
            with open(config_file, 'w') as open_config:
                self._config.write(open_config)
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


class Config(object):

    def __new__(cls, *args, **kwargs):
        self = super(Config, cls).__new__(cls)
        self.__init__(*args, **kwargs)
        return self._get_config()

    def __init__(self, config_section):
        self._config_section = config_section
        self._config_parser = SafeConfigParser()
        config_dirs = [
            ETC_DIR,
            HOME_DIR,
        ]
        config_paths = [os.path.join(conf_dir, CONFIG_FILENAME) for conf_dir in config_dirs]
        for config_path in config_paths:
            self._config_parser.read(config_path)
        self.config = self._get_config()

    def _get_config(self):
        try:
            config_items = self._config_parser.items(self._config_section)
        except NoSectionError:
            pass
        else:
            return {opt: val for opt, val in config_items}
        raise ConfigFileMissingException


def main():
    with simple_logger():
        config_creator = ConfigCreator()
        config_creator.create_config_file()


if __name__ == '__main__':
    main()
