from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.threading import Manager
from i3pystatus.core.util import convert_position
from i3pystatus.core.command import run_through_shell


class Module(SettingsBase):
    output = None
    position = 0

    settings = ('on_clicks', "Dict of callback called on click (also mouseweel events)",
                # 'on_rightclick', "Callback called on right click (string)",
                # 'on_upscroll', "Callback called on scrolling up (string)",
                # 'on_downscroll', "Callback called on scrolling down (string)",
                )

    on_clicks = {}
    # on_rightclick = None
    # on_upscroll = None
    # on_downscroll = None

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def inject(self, json):
        if self.output:
            if "name" not in self.output:
                self.output["name"] = self.__name__
            self.output["instance"] = str(id(self))
            if (self.output.get("color", "") or "").lower() == "#ffffff":
                del self.output["color"]
            json.insert(convert_position(self.position, json), self.output)

    def run(self):
        pass

    def on_click(self, button):
        """
        Maps a click event (include mousewheel events) with its associated callback.
        It then triggers the callback depending on the nature (ie type) of
        the callback variable:
        1. if null callback, do nothing
        2. if it's a python function ()
        3. if it's the name of a method of the current module (string)

        To setup the callbacks, you can set the settings 'on_leftclick',
        'on_rightclick', 'on_upscroll', 'on_downscroll'.

        For instance, you can test with:
        ::

            status.register("clock",
                    format=[
                        ("Format 0",'Europe/London'),
                        ("%a %-d Format 1",'Europe/Dublin'),
                        "%a %-d %b %X format 2",
                        ("%a %-d %b %X format 3", 'Europe/Paris'),
                    ],
                    on_leftclick= ["urxvtc"] , # launch urxvtc on left click
                    on_rightclick= ["scroll_format", 2] , # update format by steps of 2
                    on_upscroll= [print, "hello world"] , # call python function print
                    log_level=logging.DEBUG,
                    )
        """

        def map_name_to_button_id(button):
            conv = {
            "left": 1,
            "middle": 2,
            "right": 3,
            "wheelup": 4,
            "wheeldown": 5,
            }

            return getattr(conv, button, button)

        def split_callback_and_args(cb):
            if isinstance(cb, list):
                return cb[0], cb[1:]
            else:
                return cb, []

        # cb = None
        button = map_name_to_button_id(button)
        cb = getattr(self.on_clicks, button, None)
        # if button == 1:  # Left mouse button
        #     cb = self.on_leftclick
        # elif button == 3:  # Right mouse button
        #     cb = self.on_rightclick
        # elif button == 4:  # mouse wheel up
        #     cb = self.on_upscroll
        # elif button == 5:  # mouse wheel down
        #     cb = self.on_downscroll
        # else:
            # self.logger.info("Button '%d' not handled yet." % (button))
            # return

        if not cb:
            self.logger.info("No cb attached to click %d" % button)
            return
    
        cb, args = split_callback_and_args(cb)
        self.logger.debug("cb=%s args=%s" % (cb, args))

        if callable(cb):
            return cb(self)
        elif hasattr(self, cb):
            return getattr(self, cb)(*args)
        else:
            return run_through_shell(cb, *args)

    def move(self, position):
        self.position = position
        return self


class IntervalModuleMeta(type):
    """Add interval setting to `settings` attribute if it does not exist."""

    def __init__(cls, name, bases, namespace):
        super(IntervalModuleMeta, cls).__init__(name, bases, namespace)
        if not hasattr(cls, 'settings'):
            cls.settings = tuple()
        if 'interval' not in SettingsBase.flatten_settings(cls.settings):
            cls.settings += ('interval', )


class IntervalModule(Module, metaclass=IntervalModuleMeta):
    interval = 5  # seconds
    managers = {}

    def registered(self, status_handler):
        if self.interval in IntervalModule.managers:
            IntervalModule.managers[self.interval].append(self)
        else:
            am = Manager(self.interval)
            am.append(self)
            IntervalModule.managers[self.interval] = am
            am.start()

    def __call__(self):
        self.run()

    def run(self):
        """Called approximately every self.interval seconds

        Do not rely on this being called from the same thread at all times.
        If you need to always have the same thread context, subclass AsyncModule."""
