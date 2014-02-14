###
# Copyright (c) 2014, Stacey Ell
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import time
from supybot.commands import wrap
import supybot.callbacks as callbacks
import yshi.games.greed as greed
from collections import namedtuple


try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Greed')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


def _stringify_group(group):
    return u' '.join(map(str, group))


def _humanized_group_score(group):
    score = greed.calculate_score_group(group)
    return u'{} => {}'.format(_stringify_group(group[0]), score)


LastPlayerRecord = namedtuple('LastPlayerRecord', [
    'nick', 'score', 'when'
])


class Greed(callbacks.Plugin):
    """greed

    Simple dice game. Rules: https://en.wikipedia.org/wiki/Greed_(dice_game)
    """
    def __init__(self, *args, **kwargs):
        super(Greed, self).__init__(*args, **kwargs)
        self._channel_data = {}

    def _add_play(self, channel, nick, score):
        if channel not in self._channel_data:
            self._channel_data[channel] = \
                LastPlayerRecord(nick, score, time.time())
            return
        prev_play = self._channel_data[channel]
        del self._channel_data[channel]
        if prev_play.score < score:
            winner = nick
        elif prev_play.score == score:
            winner = None
        elif prev_play.score > score:
            winner = prev_play.nick
        else:
            assert False
        return prev_play.score == score, winner

    def _can_play(self, channel, nick):
        if channel not in self._channel_data:
            return False
        if not self._channel_data[channel]:
            return False
        return self._channel_data[channel].nick == nick

    def greed(self, irc, msg, args):
        """

        Rolls"""
        (channel, text) = msg.args
        if irc.isChannel(channel) and self._can_play(channel, msg.nick):
            fmt_str = u"Oh you, {}! You can't go twice in a row!"
            irc.reply(_(fmt_str.format(msg.nick)), prefixNick=False)
            return
        roll_result = sorted(greed.dice_roll())
        groups = greed.group_roll(roll_result)
        score = greed.calculate_score(groups)
        counting_info = u', '.join(map(_humanized_group_score, groups))
        winner = None
        if irc.isChannel(channel):
            winner = self._add_play(channel, msg.nick, score)
        irc.reply(_(u'you rolled ({}) for {} points ({})'.format(
            _stringify_group(roll_result), score, counting_info)))
        if winner is not None:
            tie, winner_nick = winner
            if tie:
                irc.reply(_(u'No winner'), prefixNick=False)
            else:
                irc.reply(_(u'{} wins!'.format(winner_nick)), prefixNick=False)

    greed = wrap(greed)

Class = Greed


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
