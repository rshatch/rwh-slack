This is a rewrite of the [Random Word Hell](http://wiki.dwscoalition.org/notes/Random_Word_Hell) perl code. It's intended for Slack rather than IRC, and requires the `slackclient` python library. Add a bot user to your workplace, and then export the token as `SLACK_BOT_TOKEN` in your environment variables.

TODO:
- save items to disk in case the bot goes down
- ratelimit adding things to hell to prevent botspam? 
