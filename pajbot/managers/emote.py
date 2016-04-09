import json
import logging
from collections import UserDict

from pajbot.apiwrappers import APIBase
from pajbot.managers.db import DBManager
from pajbot.models.emote import Emote

log = logging.getLogger(__name__)


class BTTVEmoteManager:
    def __init__(self, emote_manager):
        from pajbot.apiwrappers import BTTVApi
        self.emote_manager = emote_manager
        self.bttv_api = BTTVApi()
        self.global_emotes = []
        self.channel_emotes = []

    def update_emotes(self):
        log.debug('Updating BTTV Emotes...')
        global_emotes = self.bttv_api.get_global_emotes()
        channel_emotes = self.bttv_api.get_channel_emotes(self.emote_manager.streamer)

        self.global_emotes = [emote['code'] for emote in global_emotes]
        self.channel_emotes = [emote['code'] for emote in channel_emotes]

        self.emote_manager.bot.mainthread_queue.add(self._add_bttv_emotes,
                                                    args=[global_emotes + channel_emotes])

    def _add_bttv_emotes(self, emotes):
        for emote in emotes:
            key = 'custom_{}'.format(emote['code'])
            if key in self.emote_manager.data:
                self.emote_manager.data[key].emote_hash = emote['emote_hash']
            else:
                self.emote_manager.add_emote(**emote)
        log.debug('Added {} emotes'.format(len(emotes)))


class EmoteManager(UserDict):
    def __init__(self, bot):
        UserDict.__init__(self)
        self.bot = bot
        self.streamer = bot.streamer
        self.db_session = DBManager.create_session()
        self.custom_data = []
        self.bttv_emote_manager = BTTVEmoteManager(self)

        self.bot.execute_delayed(5, self.bot.action_queue.add, (self.bttv_emote_manager.update_emotes, ))
        self.bot.execute_every(60 * 60 * 2, self.bot.action_queue.add, (self.bttv_emote_manager.update_emotes, ))

        # Used as caching to store emotes
        self.global_emotes = []

    def commit(self):
        self.db_session.commit()

    def reload(self):
        self.data = {}
        self.custom_data = []

        num_emotes = 0
        for emote in self.db_session.query(Emote):
            emote.manager = self
            num_emotes += 1
            self.add_to_data(emote)

        log.info('Loaded {0} emotes'.format(num_emotes))
        return self

    def add_emote(self, emote_id=None, emote_hash=None, code=None):
        emote = Emote(self, emote_id=emote_id, emote_hash=emote_hash, code=code)
        self.add_to_data(emote)
        self.db_session.add(emote)
        return emote

    def add_to_data(self, emote):
        if emote.emote_id:
            self.data[emote.emote_id] = emote
            if emote.code:
                self.data[emote.code] = emote
        else:
            self.custom_data.append(emote)
            if emote.code:
                self.data['custom_' + emote.code] = emote

    def __getitem__(self, key):
        if key not in self.data:
            try:
                # We can only dynamically add emotes that are ID-based
                value = int(key)
            except ValueError:
                return None

            log.info('Adding new emote with ID {0}'.format(value))
            self.add_emote(emote_id=value)

        return self.data[key]

    def find(self, key):
        log.info('Finding emote with key {0}'.format(key))
        try:
            emote_id = int(key)
        except ValueError:
            emote_id = None

        if emote_id:
            return self.data[emote_id]
        else:
            key = str(key)
            if len(key) > 0 and key[0] == ':':
                key = key.upper()
            if key in self.data:
                return self.data[key]
            else:
                for emote in self.custom_data:
                    if emote.code == key:
                        return emote

        return None

    def get_global_emotes(self, force=False):
        if len(self.global_emotes) > 0 or force is True:
            return self.global_emotes

        """Returns a list of global twitch emotes"""
        base_url = 'http://twitchemotes.com/api_cache/v2/global.json'
        log.info('Getting global twitch emotes!')
        try:
            api = APIBase()
            message = json.loads(api._get(base_url))
        except ValueError:
            log.error('Invalid data fetched while getting global emotes!')
            return False

        for code in message['emotes']:
            self.global_emotes.append(code)

        return self.global_emotes

    def get_global_bttv_emotes(self):
        emotes_full_list = self.bttv_emote_manager.global_emotes
        emotes_remove_list = ['aplis!', 'Blackappa', 'DogeWitIt', 'BadAss', 'Kaged', '(chompy)', 'SoSerious', 'BatKappa', 'motnahP']

        return list(set(emotes_full_list) - set(emotes_remove_list))