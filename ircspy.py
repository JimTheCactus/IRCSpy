#! /usr/bin/env python
#
# Example program using irc.bot.
#
# Joel Rosdahl <joel@rosdahl.net>

"""A simple example bot.

This is an example bot that uses the SingleServerIRCBot class from
irc.bot.  The bot enters a channel and listens for commands in
private messages and channel traffic.  Commands in channel messages
are given by prefixing the text by the bot name followed by a colon.
It also responds to DCC CHAT invitations and echos data sent in such
sessions.

The known commands are:

    stats -- Prints some channel information.

    disconnect -- Disconnect the bot.  The bot will try to reconnect
                  after 60 seconds.

    die -- Let the bot cease to exist.

    dcc -- Let the bot invite you to a DCC CHAT connection.
"""

import irc.bot
import irc.strings
import threading
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

class TestBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.lcdmutex = threading.RLock()
        with self.lcdmutex:
            self.lcd = Adafruit_CharLCDPlate()
            self.lcd.clear()
            self.lcd.backlight(self.lcd.ON)
            self.line1 = "IRC Spy: INIT"
            self.line2 = ""
            self.line1offset = 0
            self.line2offset = 0
            self.manifold.execute_every(.2,self._do_lcd)
    def _set_line1(self,text):
        with self.lcdmutex:
            self.line1 = text
            self.line1offset = -3
    def _set_line2(self,text):
        with self.lcdmutex:
            self.line2 = text
            self.line2offset = -3
    def _do_lcd(self):
        with self.lcdmutex:
            self.lcd.home()
            l1offset = self.line1offset
            # Order is important here, the first one can make vastly negative numbers for short messages. The second will truncate that to 0.
            if l1offset > len(self.line1)-16:
                l1offset = len(self.line1)-16
            if l1offset < 0:
                l1offset = 0
            l2offset = self.line2offset
            if l2offset > len(self.line2)-16:
                l2offset = len(self.line2)-16
            if l2offset < 0:
                l2offset = 0
            msg = self.line1[l1offset:l1offset+16]+"                \n"+self.line2[l2offset:l2offset+16]+"                "
            self.lcd.message(msg)
            if len(self.line1) > 16:
                self.line1offset = self.line1offset + 1
            if len(self.line2) > 16:
                self.line2offset = self.line2offset + 1
            if self.line1offset > len(self.line1)-16+3:
                self.line1offset = -3
            if self.line2offset > len(self.line2)-16+3:
                self.line2offset = -3
    def on_action(self,c,e):
        self.lcd.clear()
        plain_nick = e.source.split("!")[0] + ">" + e.target
        self._set_line1(plain_nick)
        self._set_line2("*" + e.arguments[0])
        return 
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        self.lcd.clear()
	self._set_line1("IRC Spy: Join")
        self._set_line2(self.channel)
        c.join(self.channel)

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        self.lcd.clear()
        plain_nick = e.source.split("!")[0] + ">" + e.target
        self._set_line1(plain_nick)
        self._set_line2(e.arguments[0])
        return 

    def on_dccmsg(self, c, e):
        pass

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

def main():
    import sys
    if len(sys.argv) < 4 and len(sys.argv) > 5:
        print("Usage: testbot <server[:port]> <channel> <nickname> [password]")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]

    bot = TestBot(channel, nickname, server, port)
    if len(sys.argv) == 5:
        bot.server_list[0].password=sys.argv[4]
    bot.start()

if __name__ == "__main__":
    main()
