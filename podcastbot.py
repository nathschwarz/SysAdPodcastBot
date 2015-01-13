#!/usr/bin/env python3
#License: GPL v2

import praw
import yaml
import logging
import argparse
import re
import github3

user_agent = 'podcast/github bot for /r/sysadmin v1.0 by /u/nath_schwarz'
conf_file = 'podcastbot.conf'

issue_body = "Submitted by: [{0}](https://reddit.com/u/{0})\nContext: {1}\nNote: {2}"
postfix = ''

#globals
r = None
g = None
conf = None
logger = None

def load_config():
    """Loads configuration from 'cspaperbot.conf' and returns it."""
    global conf
    try:
        with open(conf_file, 'r') as f:
            conf = yaml.load(f)
    except Exception as e:
        logger.error(e)

def login():
    """Logs in to reddit and github with given username and password."""
    global r, g
    try:
        r = praw.Reddit(user_agent = user_agent)
        r.login(conf['username'], conf['password'])
        g = github3.login(conf['gh_username'], conf['gh_password'])
        logger.info('Logins successful')
    except Exception as e:
        logger.error(e)

def reply_to(comment, body):
    """Reply to given comment with given text. Appends postfix automatically."""
    logger.info('Commented on ' + comment.id + ":\n" + body)
    comment.reply(body + '  \n' + postfix)

def open_issue(title, submitter, context, note):
    return g.create_issue(conf['repo_owner'], conf['repository'], title, body = issue_body.format(submitter, context, note)).html_url

def check_messages():
    for message in r.get_unread():
        if 'username mention' in message.subject:
            line = re.search('/u/' + conf['username'] + ' (.+) {,2}\n{1,2}', message.body)
            title = message.submission.title
            if message.is_root:
                context = message.submission.permalink
            else:
                title = message.author + ' on ' + title
                #Because PRAW is inconsistent
                context = message.permalink + '?context=3'
            reply_to(message, open_issue(title, message.author, context, line))
            message.mark_as_read()
    logger.info('Unread processed')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("--stdout", action="store_true", help="print log output to stdout")
    args = parser.parse_args()

    global logger
    if args.verbose:
        logging.basicConfig(level = logging.INFO)
    else:
        logging.basicConfig(level = logging.ERROR)
    if not args.stdout:
        logging.basicConfig(filename = 'bot.log')
    logger = logging.getLogger('podcastbot')

    load_config()
    login()
    check_messages()
    r.clear_authentication()

if __name__ == "__main__":
    main()
