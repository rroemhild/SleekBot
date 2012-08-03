"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import socket
import dns.resolver

from sleekbot.commandbot import botcmd, CommandBot, denymsg
from sleekbot.commandbot import parse_args, ArgError
from sleekbot.plugbot import BotPlugin


class Networking(BotPlugin):
    """ A set of Networktools for the bot.
    """

    @botcmd(name='resolve', usage='[a|mx|txt] host',
            allow=CommandBot.msg_from_member)
    @denymsg('You are insufficiently cool, go away')
    def handle_resolve(self, command, args, msg):
        """Handle resolve queries by rdatatype."""

        try:
            args = parse_args(args, (('rdtype', ('a', 'mx', 'txt')),
                                     ('host', str)))
        except ArgError as ex:
            return ex.msg

        try:
            answers = dns.resolver.query(args.host, args.rdtype)
        except dns.rdatatype.UnknownRdatatype:
            return "Unknown RData Type."
        except dns.resolver.NXDOMAIN:
            return "Name or service not known."

        retval = []
        # A record
        if answers.rdtype == 1:
            for rdata in answers:
                retval.append("%s has address %s" % (args.host, rdata))
        # MX record
        elif answers.rdtype == 15:
            for rdata in answers:
                retval.append("Host %s has preference %s" % (rdata.exchange,
                                                              rdata.preference))
        # TXT record
        elif answers.rdtype == 16:
            for rdata in answers:
                retval.append("%s has TXT %s" % (args.host, rdata))

        if retval:
            infostr = "Resolved %s record for %s:" % (args.rdtype.upper(),
                                                     args.host)
            retval = [infostr] + retval
            return "\n".join(retval)
        else:
            return "No data."

    @botcmd(name='host', usage='[ip|hostname]',
            allow=CommandBot.msg_from_member)
    @denymsg('You are insufficiently cool, go away')
    def handle_host(self, command, args, msg):
        """Get lookup ip or hostname."""

        try:
            args = parse_args(args, (('addr', str),))
        except ArgError as ex:
            return ex.msg

        try:
            answer = socket.gethostbyaddr(args.addr)
        except socket.gaierror:
            return "Name or service not known."
        except socket.error:
            return "Unknown host."

        return "%s has address %s" % (answer[0], answer[2][0])
