"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import random

from sleekbot.commandbot import botcmd
from sleekbot.plugbot import BotPlugin


class RobberFilter():
    """ Replace each consonant X by XoX
    """
    def __call__(self, text):
        consonants = 'bcdfghjklmnpqrstvwxz'
        outstring = ''
        for char in text:
            if char in consonants:
                outstring = outstring + char + 'o' + char
            else:
                outstring += char
        return outstring


class LeetFilter():
    """ Replace each letter with a random symbol taken from a list
    """
    def __init__(self):
        self.mappings = {
            'a': ['4', '/\\', '@', '/-\\', '^'],
            'b': ['8', '6', '13', '!3'],
            'c': ['[', '<', '(', '{'],
            'd': [')', '|)', '[)', '0', 'T)'],
            'e': ['3', '&', '[-'],
            'f': ['|=', '|#', '/='],
            'g': ['6', '&', '9', 'C-'],
            'h': ['#', '/_/', '[-]', '|-|', '}{'],
            'i': ['1', '!', '|', ']'],
            'j': ['_|', '_/', '(/'],
            'k': ['X', '|<', '|(', '|{'],
            'l': ['1', '|', '|_'],
            'm': ['|v|', '|\\//|'],
            'n': ['^/', '/\\/', '[]\\'],
            'o': ['0', '()', '[]'],
            'p': ["|*", "|>", "9", "|7"],
            'q': ['(_,)', '()_', '0_', '<|'],
            'r': ['2', '|?', '/2', '|^', '12', 'l2'],
            's': ['5', '$', 'z'],
            't': ['7', '+', '-|-', '1', '\'][\''],
            'u': ['(_)', '|_|', 'v', 'L|'],
            'v': ['\\/'],
            'w': ['\\/\\/', 'vv', '\\^/', '\\|/'],
            'x': ['%', '><', '}{', ')('],
            'y': ['j', '`/'],
            'z': ['2', '~/_', '%', '>_', '7_']
        }
        pass

    def __call__(self, text):
        """ Filter text. """
        result = ''
        for char in text:
            leets = self.mappings.get(char, [char])
            if len(leets) == 0:
                continue
            result += leets[random.randint(0, len(leets) - 1)]
        return result


class ChefFilter(object):
    """    -------------------- Swedish Chef -----------------------

    chef = {
      { th = "t" },

      { ow = "o"},
      {["([^%w])o"] = "%1oo",
      O = "Oo"},

      {au = "oo",
      u = "oo", U = "Oo"},
      {["([^o])o([^o])"] = "%1u%2"},
      {ir = "ur",

      an = "un", An = "Un", Au = "Oo"},

      {e = "i", E = "I"},

      { i = function () return select(math.random(2), "i", "ee"); end },

      {a = "e", A = "E"},

      {["e([^%w])"] = "e-a"},
      {f = "ff"},

      {v = "f", V = "F"},
      {w = "v", W = "V"} };

    function swedish(english)
            eng, url = english:match("(.*)(http://.*)$"); -- (URLs at the END of text will be preserved)
            if eng then english = eng; end

            for _,v in ipairs(chef) do
                    for k,v in pairs(v) do
                            english = english:gsub(k,v);
                    end
            end
            english = english:gsub("the", "zee");
            english = english:gsub("The", "Zee");
            english = english:gsub("tion", "shun");
            return tostring(english..((url and url) or ""));
    end
    """
    def __init__(self):
        pass

    def __call__(self, text):
        return text


class Filter(BotPlugin):
    """A plugin to filter text."""

    def _on_register(self):
        """ Register available filters.
        """
        self.available_filters = {}
        self.available_filters['leet'] = LeetFilter()
#        self.availableFilters['chef'] = chefFilter()
        self.available_filters['robber'] = RobberFilter()

    @botcmd(name='filter', usage='[filter type] [text]')
    def handle_filter(self, command, args, msg):
        """Parses the text through a filter"""
        if args == None or args == "" or len(args.split(" ")) < 2:
            return "Insufficient information, please check help."
        language = args.split(" ")[0].lower()
        text = " ".join(args.split(" ")[1:])
        if language not in self.available_filters.keys():
            return "Language %s not available" % language
        return self.available_filters[language](text)
