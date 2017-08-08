#!/usr/bin/python

from rabbit_tools.base import RabbitToolBase


class PurgeQueueTool(RabbitToolBase):

    args = {
        'queue_name': {
            'help': 'Name of a queue to purge.',
            'nargs': '?',
        },
    }
    description = ('Purge an AMQP queue. Do not pass a queue\'s name as an argument, '
                   'if you want to choose it from the list.')

    client_method_name = "purge_queue"

    queue_not_affected_msg = "Cannot purge the queue"
    queues_affected_msg = "Successfully purged queues"
    no_queues_affected_msg = "No queues have been purged."


def main():
    purge_queue_tool = PurgeQueueTool()
    try:
        purge_queue_tool.run()
    except KeyboardInterrupt:
        print "Bye"


if __name__ == '__main__':
    main()
