#!/usr/bin/env python
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import math

import random
import string

import inspect

from sleekbot.commandbot import botcmd, parse_args, ArgError
from sleekbot.plugbot import BotPlugin
import sleekbot.confighandler as confighandler

import logging

# make a list of safe functions
SAFE_LIST = ['math', 'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', \
'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot', 'ldexp', \
'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', \
'tanh', 'abs']
# use the list to filter the local namespace
SAFE_DICT = dict([(k, getattr(locals()['math'], k, None)) for k in SAFE_LIST])
SAFE_DICT['d'] = random.randint

class BotMath(BotPlugin):
    """A nerdy plugin for rolling complex or simple formulas."""

    def __init__(self, passgen={}):
        # Passgen defaults
        BotPlugin.__init__(self)
        self._passgen = passgen

    @botcmd(usage='[math expression]')
    def calc(self, command, args, msg):
        """Does a mathematical calculation
        You can do simple calculations such as 2+3
        Or more complex such as sin(1.5*pi)
        """
        try:
            return str(eval(args, {"__builtins__": None}, SAFE_DICT))
        except:
            return "Nothing to calculate."

    @botcmd(usage='[A B|B]')
    def random(self, command, args, msg):
        """Returns a random integer in range A - B or 1 - B."""

        try:
            args = parse_args(args, (('first', int), ('second', 1)))
        except ArgError as error:
            return error.msg

        if args.first > args.second:
            args.first, args.second = args.second, args.first

        ran = random.randint(args.first, args.second)
        if msg['type'] == 'groupchat':
            return "%s rolls %d (%s - %s)" % \
                   (msg['mucnick'], ran, args.first, args.second)
        else:
            return "%d (%s - %s)" % (ran, args.first, args.second)

    @botcmd(usage='[dice calculation]')
    def roll(self, command, args, msg):
        """Rolls dice for you. d(n) is a dice with n sides
        Example: roll (1 + d(6) + 2*d(10) + 5 + d(4) * 2 """
        try:
            return str(eval(args, {"__builtins__": None}, SAFE_DICT))
        except:
            return "Nothing to roll."

    @botcmd(usage='[alpha|alphanum|numbers|all] [length]')
    def passgen(self, command, args, msg):
        """Generates random passwords."""

        defaults = {'choice': 'all', 'length': 8, 'max_length': 100}
        choices = {'alpha': string.letters,
                   'alphanum': string.letters + string.digits,
                   'numbers': string.digits,
                   'all': string.letters + string.digits + string.punctuation}

        if args.count(" ") > 0:
            choice, length = args.split(" ", 1)
            choice, length = choice.strip(' '), length.strip(' ')
        elif not args == '':
            if args.isdigit():
                choice, length = self._passgen.get('choice', defaults['choice']),\
                                 args.strip(' ')
            else:
                choice, length = args.strip(' '),\
                            str(self._passgen.get('length', defaults['length']))
        else:
            choice, length = self._passgen.get('choice', defaults['choice']),\
                           str(self._passgen.get('length', defaults['length']))

        if not choice in choices:
            return "Choices are alpha, alphanum, numbers or all."
        if not length.isdigit():
            return "Length should be a number."
        if int(length) > int(self._passgen.get('max_length',
                                               defaults['max_length'])):
            return "Do you really need such a long password?"

        return "".join(random.choice(choices[choice]) \
                       for x in range(int(length)))
