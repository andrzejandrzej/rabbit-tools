# rabbit-tools
A set of tools for convenient administration of RabbitMQ queues.

## Getting Started

The project is intended to wrap a set of tools, with similar interfaces, making the basic administration of AMQP queues easier. Currently, rabbit-tools work with [RabbitMQ](http://www.rabbitmq.com/).

### Prerequisites

* Python 2.7 (migration to Python 3 is planned in the near future)
* Virtual Env (optionally)
* RabbitMQ server hosted somewhere

### Installing

rabbit-tools are installed simply by a Python setup script, preferably inside a Vritual Env.

```
python setup.py install
```

Then you should create a new config file with RabbitMQ connection parameters, using a command:

```
rabbit_tools_config
```

## Usage

Currently available commands:
* **rabpurge** - purge selected queues
* **rabdel** - delete selected queues

You can run these commands with or without arguments. Calling it without arguments runs a script from the beginning, viewing a list of available queues with numbers assigned, to make choosing of queues easier, and awaits for an input from user. It accepts queue numbers as valid input.
Otherwise, you can pass chosen queue names, separated by space, as arguments, or *all* to choose all queues.

For example, to purge the *parsed* and *validated* queues:

```
rabpurge parsed validated
```

### Multi-choices, ranges

The *interactive* mode (without arguments passed) allows to conveniently choose many queues. There is the "all" option, but you can also separate single queue numbers with spaces and/or commas, or you can choose a range of numbers by defining first and last number of range separated by **-**.
Examples:

Numbers 1, 3, 6 and 8:
```
Queue number ('all' to choose all / 'q' to quit'): 1 3,  6,8
```

Range of numbers from 2 to 6 (inclusive):
```
Queue number ('all' to choose all / 'q' to quit'): 2-6
```

## Authors

* **Andrzej Dębicki** - [andrzejandrzej](https://github.com/andrzejandrzej)


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
