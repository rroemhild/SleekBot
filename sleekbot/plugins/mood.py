"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

from xml.etree import cElementTree as ET

from sleekbot.plugbot import BotPlugin

MOODS = ['afraid', 'amazed', 'angry', 'annoyed', 'anxious', 'aroused', \
         'ashamed', 'bored', 'brave', 'calm', 'cold', 'confused', 'contented', \
         'cranky', 'curious', 'depressed', 'disappointed', 'disgusted', \
         'distracted', 'embarrassed', 'excited', 'flirtatious', 'frustrated', \
         'grumpy', 'guilty', 'happy', 'hot', 'humbled', 'humiliated', \
         'hungry', 'hurt', 'impressed', 'in_awe', 'in_love', 'indignant', \
         'interested', 'intoxicated', 'invincible', 'jealous', 'lonely', \
         'mean', 'moody', 'nervous', 'neutral', 'offended', 'playful', \
         'proud', 'relieved', 'remorseful', 'restless', 'sad', 'sarcastic', \
         'serious', 'shocked', 'shy', 'sick', 'sleepy', 'stressed', \
         'surprised', 'thirsty', 'worried']

class Mood(BotPlugin):
    """Set the bot's mood."""

    def _on_register(self):
        """ Creats a mood form and publish and adhoc command
        """
        self.pubsub = self.bot.plugin['xep_0060']
        self.xform = self.bot.plugin['xep_0004']
        self.adhoc = self.bot.plugin['xep_0050']
        self.moods = MOODS

        frm = self.xform.makeForm('form', "Set Mood")
        moods = frm.addField('mood', 'list-single', 'Mood')
        for mood in self.moods:
            moods.addOption(mood, mood.title())
        frm.addField('desc', 'text-single', 'Description')
        self.adhoc.add_command('setmood', 'Set Mood', frm, self.handler)

    def handler(self, form, sessid):
        """ Handles Form
        """
        value = form.getValues()
        moodx = ET.Element('{http://jabber.org/protocol/mood}mood')
        moodel = ET.Element(value['mood'])
        text = ET.Element('text')
        text.text = value['desc']
        moodx.append(moodel)
        moodx.append(text)
        self.pubsub.setItem(self.bot.server, \
                            'http://jabber.org/protocol/mood', \
                            ((None,moodx), ))
        done = self.xform.makeForm('form', "Finished")
        done.addField('done', 'fixed', value="Mood updated.")
        return done, None, False
