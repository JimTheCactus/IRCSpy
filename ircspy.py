#! /usr/bin/env python
#
# by: JimTheCactus <jimthecactus@gmail.com>
# Derived heavily from an example by Joel Rosdahl <joel@rosdahl.net>

# Depends on irc and Adafruit's CharLCDPlate modules. Also requires that you actually have an Adafruit CharLCDPlate

import irc.bot
import irc.strings
import threading
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

class TestBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667,password=None):
        irc.bot.SingleServerIRCBot.__init__(self, [irc.bot.ServerSpec(server,port,password)], nickname, nickname)
        self.channel = channel
        # Create a mutex to handle our calls to the LCD
        self.lcdmutex = threading.RLock()
        # And initialize the various properties.
        with self.lcdmutex:
            self.lcd = Adafruit_CharLCDPlate()
            self.lcd.clear()
            self.lcd.backlight(self.lcd.ON)
            self.line1 = "INFO: INIT"
            self.line2 = "IRC Spy v1.0"
            self.lcd.message("{0:<16}\n{1:<16}".format(self.line1,self.line2))

            self.startpause = 3 # This causes the message to pause 3 extra ticks at the start. Write to it to change this delay.
            self.endpause = 3 # This causes the message to pause 3 extra ticks at the end. Write to it to change this delay.
            self.line1offset = -self.startpause
            self.line2offset = -self.startpause
        self.manifold.execute_every(.2,self._do_lcd)

    def _set_line1(self,text):
        with self.lcdmutex:
            self.line1 = text
            self.line1offset = -self.startpause

    def _set_line2(self,text):
        with self.lcdmutex:
            self.line2 = text
            self.line2offset = -self.startpause

    def _do_lcd(self):
        # Important to know: The offsets are deliberately run off the ends, both forward and backwards, to allow for some delay at the beginning
        # and end of the scroll. The cached values have the actual offsets that will be used to access the arrays and are properly monitored to
        # ensure that they're correctly in bounds.
        # The offset of an 18 character line will follow the following path:
        #  offset: -3 -2 -1  0  1  2  3  4  5 -3 -2 -1  0  1 etc...
        # loffset:  0  0  0  0  1  2  2  2  2  0  0  0  0  1 etc...
       
        with self.lcdmutex:
            # Cache the two offsets
            l1offset = self.line1offset
            l2offset = self.line2offset
            # Order is important here, the first one can make vastly negative numbers for short messages. The second will truncate that to 0.
            # Start by making sure we don't go off the end.
            if l1offset > len(self.line1)-16:
                l1offset = len(self.line1)-16
            if l2offset > len(self.line2)-16:
                l2offset = len(self.line2)-16
            # Then check to make sure we aren't off the beginning as well.
            if l1offset < 0:
                l1offset = 0
            if l2offset < 0:
                l2offset = 0
            
            # Build up a message string with exactly 16 characters for each line. This will purge things without the flicker
            # of a clear() command since it causes an overwrite.
            msg = "{0:<16}\n{1:<16}".format(self.line1[l1offset:l1offset+16],self.line2[l2offset:l2offset+16])
            # Move the write cursor to the beginning and write out the message
            self.lcd.home()
            self.lcd.message(msg)

            # If we should be scrolling, move the offset ahead by one.
            if len(self.line1) > 16:
                self.line1offset = self.line1offset + 1
            if len(self.line2) > 16:
                self.line2offset = self.line2offset + 1
            # If we've gone off the end, plus some for the end of line delay, the reset back with enough for the start of line delay.
            if self.line1offset > len(self.line1)-16+self.endpause:
                self.line1offset = -self.startpause
            if self.line2offset > len(self.line2)-16+self.endpause:
                self.line2offset = -self.startpause

    def on_action(self,c,e):
        self.lcd.clear()
        plain_nick = e.source.split("!")[0]
        self._set_line1("*ACTION>" +e.target)
        self._set_line2(plain_nick + " " + e.arguments[0])
        return 

    def on_disconnect(self,c,e):
        print "Disconnected!"
        self._set_line1("ERROR:")
        self._set_line2("Disconnected")

    def on_passwdmismatch(self,c,e):
        print "Password rejected!"
        self._set_line1("ERROR:")
        self._set_line2("Bad Password")
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        print "Connected. Joining channel " + self.channel + "..."
	self._set_line1("INFO: CONNECT")
        self._set_line2("Joining...")
        c.join(self.channel)

    def on_join(self, c, e):
        print "Joined " + e.target;
        self._set_line1("INFO: JOIN")
        self._set_line2(e.target);

    def on_privmsg(self, c, e):
        self.lcd.clear()
        plain_nick = e.source.split("!")[0] + ">" + e.target
        self._set_line1(plain_nick)
        self._set_line2(e.arguments[0])
        return 

    def on_pubmsg(self, c, e):
        self.lcd.clear()
        plain_nick = e.source.split("!")[0] + ">" + e.target
        self._set_line1(plain_nick)
        self._set_line2(e.arguments[0])
        return 

def main():
    import sys
    if len(sys.argv) < 4 or len(sys.argv) > 5:
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
    if len(sys.argv) == 5:
        password = sys.argv[4]

    print "Connecting to " + sys.argv[1] + "..."
    bot = TestBot(channel, nickname, server, port,password)
    print "Listening for server..."
    bot.start()

if __name__ == "__main__":
    main()
