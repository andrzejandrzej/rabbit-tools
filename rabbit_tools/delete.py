#!/usr/bin/python

from rabbit_tools.base import RabbitToolBase


class DelQueueTool(RabbitToolBase):

    args = {
        'queue_name': {
            'help': 'Name of a queue to delete.',
            'nargs': '?',
        },
    }
    description = ('Delete an AMQP queue. Do not pass a queue\'s name as an argument, '
                   'if you want to choose it from the list. You can use choose a single queue '
                   'from dynamically generated list or enter a range (two numbers separated by'
                   ' `-`) or a sequence of numbers separated by `,`.')

    client_method_name = "delete_queue"

    queue_not_affected_msg = "Cannot delete queue"
    queues_affected_msg = "Successfully deleted queues"
    no_queues_affected_msg = "No queues have been deleted."


def main():
    del_queue_tool = DelQueueTool()
    try:
        del_queue_tool.run()
    except KeyboardInterrupt:
        print "Bye"


if __name__ == '__main__':
    main()
