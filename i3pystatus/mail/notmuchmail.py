#!/usr/bin/env python
# -*- coding: utf-8 -*-

# note that this needs the notmuch python bindings. For more info see:
# http://notmuchmail.org/howto/#index4h2
import notmuch
import configparser
import os
import io
import sys
from contextlib import redirect_stdout

from i3pystatus.mail import Backend
from i3pystatus import logger


class Notmuch(Backend):
    """
    This class uses the notmuch python bindings to check for the
    number of messages in the notmuch database with the tags "inbox"
    and "unread"
    """

    settings = (
        ("db_path", "Path to the directory of your notmuch database"),
    )

    db_path = None
    db = None

    def init(self):
        if not self.db_path:
            defaultConfigFilename = os.path.expanduser("~/.notmuch-config")
            config = configparser.RawConfigParser()

            # read tries to read and returns successfully read filenames
            config.read([
                os.environ.get("NOTMUCH_CONFIG", defaultConfigFilename),
                defaultConfigFilename
            ])

            self.db_path = config.get("database", "path")

    def _open_db(self):
        self.db = notmuch.Database(self.db_path)
        return self.db

    @property
    def unread(self):
        self.db = self.db if self.db else self._open_db()

        # only valid for python3.4
        # https://docs.python.org/3.4/library/contextlib.html#contextlib.redirect_stdout
        if sys.hexversion > 0x03040000:
            f = io.StringIO()
            with redirect_stdout(f):
                res = notmuch.Query(self.db, "tag:unread and tag:inbox").count_messages()
                if f.getvalue():
                    logger.warning("Notmuch error" + f.getvalue())
                    self.db = None
        else:
            res = notmuch.Query(self.db, "tag:unread and tag:inbox").count_messages()

        return res


Backend = Notmuch
