import os
import time
import re
import slack
from dumper import dump
from datetime import datetime, timedelta
from random import randint
import pickle
import logging as log

# basic log config.
log.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s', 
    datefmt='%m/%d/%Y %I:%M:%S %p',
    filename='bot.log',
    level=log.DEBUG
    )


# constants
EMOTED = re.compile(r"^(?:([^ ]+ly) )?(?:feed|send|da[mr]n|punt|tosse|smite|condemn|hurl|throw|kick|cast|banishe|drag|pull|consign|pushe|shove|drop|give)s (.*) (?:(?:in)?to|at) (?:heck|hell)([,\.]? +.*?)?[\.\?!]*$", flags=re.I)
SAID = re.compile(r"^(?:feed|send|da[mr]n|punt|toss|smite|condemn|hurl|throw|kick|cast|banish|drag|pull|consign|push|shove|drop|give) (.*) (?:(?:in)?to|at) (?:heck|(?:rw)?hell)([,\.]? +.*?)?[\.\?!]*$", flags=re.I)
SIMPLE = re.compile(r"^to (?:heck|hell) with (.*?)[\.\?!]*$", flags=re.I)

# instantiate Slack & Twilio clients
rtmclient = slack.RTMClient(token=os.environ.get('SLACK_BOT_TOKEN'))
items = {}

@slack.RTMClient.run_on(event='message')
def parse_slack_output(**payload):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    data = payload['data']
    channel = data['channel']
    say = said(data['text'])
    web_client = payload['web_client']
    emote = emoted(data['text'])
    simple = simple_said(data['text'])
    action = [i for i in [say, emote, simple] if i]
    if len(action) > 0:
        item = action[0]
        user = web_client.users_info(user=data['user'])
        nick = user['user']['profile']['display_name']
        my = nick + "'" if re.match(r"s$", nick, flags=re.I) else nick + "'s"
        item = re.sub(r"^(?:his|her|hir|their|my)", my, item, flags=re.I)
        item = re.sub(r"^(?:(?:him|her|hir|them)self|themselves)", nick, item, flags=re.I)
        feed_on(web_client, item, channel)
        expel(web_client, channel)
    if re.match(r"^hell.*tally[\?\.]?$", data['text'], flags=re.I):
        if channel in items:
            numitems = len(items[channel])
        else:
            numitems = 0
        tally = f"I am lord over {numitems!s} damned souls."
        web_client.chat_postMessage(channel=channel,
              text=tally, as_user=True)



def feed_on(web_client, match, channel):
    """
        This method takes an item and the channel it was fed to hell in.
        It adds the item to the list for that channel along with the time it was
        fed into hell, and then emotes eating it to the channel.
    """

    item = {"name" : match, "time" : datetime.utcnow().isoformat() }
    if channel in items:
        items[channel].append(item)
    else:
        items[channel] = [item]

    with open('hell.p', 'wb') as cucumber:
        pickle.dump( items, cucumber )
    action = f"sneaks out a scaly hand and grabs {match}!"
    web_client.chat_meMessage(channel=channel,
                          text=action, as_user=True)


def emoted(text):
    emote = EMOTED.match(text)
    if emote:
        item = ' '.join(filter(None, [emote.group(2), emote.group(3),  emote.group(1)]))
        return item
    return None


def said(text):
    say = SAID.match(text)
    if say:
        item = ' '.join(filter(None, [say.group(1), say.group(2)]))
        return item
    return None


def simple_said(text):
    say = SAID.match(text)
    if say:
        item = say.group(1)
        return item
    return None


def remove_random(channel):
    if channel in items and len(items[channel]):
        channel_items = items[channel]
        index = randint(0, len(channel_items) - 1)
        item = channel_items.pop(index)
        #FIXME: remove from file here
        return item['name'], item['time']
    else:
        return None, None


def expel(web_client, channel,rerun=False):
    if channel in items:
        numitems = len(items[channel])
    else:
        numitems = 0
    if rerun:
        percent = 100
        rerunpercent = 0  # was 20, set to 0 to stop more than two expulsions at once
    else:
        # CHANGETHIS: This section controls how often the bot will spit something
        #             out, and how often it'll trigger more than once. The default
        #             numbers will make the bot eventually reach a stable
        #             equilibrium at roughly 60 items. percent = the percentage
        #             chance of spitting something out, rerunpercent = the
        #             percentage chance that it'll spit two things out.
        if numitems <= 5:
            percent = 12
            rerunpercent = 0
        elif numitems <= 10:
            percent = 25
            rerunpercent = 0
        elif numitems <= 15:
            percent = 40
            rerunpercent = 0
        elif numitems <= 20:
            percent = 65
            rerunpercent = 2
        elif numitems <= 30:
            percent = 80
            rerunpercent = 4
        elif numitems <= 45:
            percent = 82
            rerunpercent = 5
        elif numitems <= 60:
            percent = 85
            rerunpercent = 6
        else:
            percent = 95
            rerunpercent = 10

    chance = randint(1, 100)
    rerunchance = randint(1, 100)
    if chance <= percent:
        random, time = remove_random(channel)
        if random:
            if time:
                now = datetime.utcnow()
                duration = time_pp(now - datetime.fromisoformat(time))
            else:
                duration = "an unknown amount of time"

        if rerun:
            emit = "continue to"
        else:
            emit = "emit a sudden"

        action = f"Hell's depths {emit} roar as it expels {random}. (stayed in Hell for {duration})"
        web_client.chat_meMessage(channel=channel,
                          text=action, as_user=True)
        if rerunchance <= rerunpercent:
            expel(web_client, channel, rerun=True)


def time_pp(delta):
    days = delta.days
    hours = delta.seconds / 3600
    minutes = (delta.seconds % 3600 ) / 60
    seconds = (delta.seconds % 3600) % 60
    days_str = "{0:d} days".format(days) if days > 0 else None
    hours_str = "{0:d} hours".format(hours) if hours > 0 else None
    min_str = "{0:d} minutes".format(minutes) if minutes > 0 else None
    sec_str = "{0:d} seconds".format(seconds) if seconds > 0 else "less than a second."
    duration = ', '.join(filter(None, [days_str, hours_str, min_str, sec_str]))
    return duration


try:
    with open('hell.p', 'wb') as cucumber:
        items = pickle.load(cucumber)
    log.info("Successfully unpickled items.")
except Exception as e:
    log.warning("Something went wrong unpickling.")
    log.warning(e)

rtmclient.start()

