"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

from xml.etree import cElementTree as ET

OAUTH_REQ = "<iq type='get' xmlns='jabber:client'>" + \
            "<query xmlns='urn:xmpp:oauth:request' /></iq>"
OAUTH_ACC = "<iq type='get' xmlns='jabber:client'>" + \
            "<query xmlns='urn:xmpp:oauth:access' /></iq>"
            
class OAuth(object):
    """ A Plugin to provide OAuth authentication. """
    
    def __init__(self, bot, config):
        self.bot = bot
        #print dir(self.bot)
        self.config = config
        self.xmpp = self.bot
        self.bot.add_handler(OAUTH_REQ, self.handle_request, threaded=True)
        self.bot.add_handler(OAUTH_ACC, self.handle_access, threaded=True)

    def handle_request(self, xml):
        """ Handles a OAuth request. """
        oauth = xml.find('{urn:xmpp:oauth:request}query/{urn:xmpp:oauth}oauth')
        oid = xml.get('id','0')
        if oauth is None:
            error = self.xmpp.makeIqError(oid)
            error.append(self.make_error())
            self.xmpp.send(error)
            return
        # check signature
        # generate random token and secret
        # store in DB
        res = self.xmpp.makeIqResult(oid)
        que = ET.Element('{urn:xmpp:oauth:request}query')
        res.append(que)
        que.append(self.makeOAuthToken('requestkey', 'requestsecret'))
        self.xmpp.send(res)

    def handle_access(self, xml):
        """ Handles a OAuth access. """
        oauth = xml.find('{urn:xmpp:oauth:access}query/{urn:xmpp:oauth}oauth')
        oid = xml.get('id','0')
        if oauth is None:
            error = self.xmpp.makeIqError(oid)
            error.append(self.make_error())
            return
        # check signature
        # check status of request token
        # generate random token and secret
        # store in DB
        res = self.xmpp.makeIqResult(oid)
        que = ET.Element('{urn:xmpp:oauth:request}query')
        res.append(que)
        que.append(self.make_token('accesskey', 'accesssecret'))
        self.xmpp.send(res)

    def make_token(self, token, secret):
        """ Makes an OAuth token. """
        oauth = ET.Element('{urn:xmpp:oauth:token}oauth')
        tokenxml = ET.Element('oauth_token')
        tokenxml.text = token
        secretxml = ET.Element('oauth_token_secret')
        secret.text = secret
        oauthxml.append(tokenxml)
        oauth.append(secretxml)
        return oauth
        
    def make_error(self):
        """ Makes an error. """
        cond = self.makeStanzaErrorCondition('bad-request')
        return self.xmpp.makeStanzaError(cond , 'cancel')
