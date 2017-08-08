import errno
import os
import sys


DEFAULT_CONFIG = '''[rabbit_tools]
api_url = 127.0.0.1:15672
user = guest
passwd = guest
vhost = /'''

CONFIG_FILENAME = 'rabbit_tools.conf'
ETC_DIR = '/etc/rabbit_tools'
HOME_DIR = os.path.expanduser('~/.rabbit_tools')


def answer_yes_no(msg):
    positive_answers = ['y', 't', 'yes', 'ok']
    negative_answers = ['n', 'no']
    answer = raw_input(msg + ' (y/n)' + '\n')
    if not answer or answer.lower() in positive_answers:
        return True
    elif answer.lower() in negative_answers:
        return False
    else:
        return None


def write_config(dir_path):
    config_file = os.path.join(dir_path, CONFIG_FILENAME)
    if os.path.exists(config_file):
        if not answer_yes_no("Config file already exists, do you want to overwrite it?"):
            return config_file
    try:
        with open(config_file, 'w') as open_config:
            open_config.write(DEFAULT_CONFIG)
        print 'Default config was written to: {}. You can edit it now.'.format(config_file)
        return True
    except IOError as e:
        if e.errno == errno.EACCES:
            print "No permission to write to: {}".format(config_file)
        elif e.errno == errno.EISDIR:
            print "File {} is a directory!".format(config_file)
        return False
    except Exception as e:
        print "Unknown error while writing to: {}. Message: {}".format(config_file, e.message)
        return False


def make_dir(dir_path):
    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        elif e.errno == errno.EACCES:
            print "No permission to write to: {}".format(dir_path)
            return False
        else:
            return False
    config_path = write_config(dir_path)
    return config_path


def create_config_file():
    if answer_yes_no("Do you want to write a new config file?"):
        if not make_dir(ETC_DIR):
            print "Could not write config file to: {}, using: {}".format(ETC_DIR, HOME_DIR)
            if not make_dir(HOME_DIR):
                sys.exit("Failed to write a config file.")


if __name__ == '__main__':
    create_config_file()
