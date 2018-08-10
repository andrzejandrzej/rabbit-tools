# -*- coding: utf-8 -*-

import logging

from rabbit_tools.base import RabbitToolBase
from rabbit_tools.lib import log_exceptions


logger = logging.getLogger(__name__)


class DelQueueTool(RabbitToolBase):

    description = ('Delete an AMQP queue. Do not pass a queue\'s name as an argument, '
                   'if you want to choose it from the list. You can use choose a single queue '
                   'from dynamically generated list or enter a range (two numbers separated by'
                   ' `-`) or a sequence of numbers separated by `,`.')

    client_method_name = "delete_queue"

    queue_not_affected_msg = "Cannot delete queue"
    queues_affected_msg = "Successfully deleted queues"
    no_queues_affected_msg = "No queues have been deleted."

    do_remove_chosen_numbers = True


def main():
    with log_exceptions():
        del_queue_tool = DelQueueTool()
        try:
            del_queue_tool.run()
        except KeyboardInterrupt:
            print "Bye"


if __name__ == '__main__':
    main()
