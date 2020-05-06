import arcade

from src.misc.game_constants import debug


class SoundEngine:
    soundPath = "../resources/sounds/"

    menuLoop = "loopComplex2.mp3"
    playLoop = "loopSimple.mp3"

    alert = "alert.mp3"
    click = "click.mp3"
    construction = "construction.mp3"
    unitRecruited = "unitRecruited.mp3"

    hut = "hut.mp3"
    villa = "villa.mp3"
    barracks = "barracks.mp3"

    s = arcade.load_sound(soundPath + menuLoop)

    def play_my_sound(self, msg:str):

        #s = arcade.load_sound(self.soundPath + self.menuLoop)
        # arcade.play_sound(s)

        debug(msg)

        my_msg = "menuLoop"
        stop_loop = 0

        if msg == "menuLoop":
            stop_loop = 1
            my_msg = self.menuLoop
        if msg == "playLoop":
            stop_loop = 1
            my_msg = self.playLoop
        if msg == "alert":
            my_msg = self.alert
        if msg == "click":
            my_msg = self.click
        if msg == "construction":
            my_msg = self.construction
        if msg == "unitRecruited":
            my_msg = self.unitRecruited
        if msg == "hut":
            my_msg = self.hut
        if msg == "villa":
            my_msg = self.villa
        if msg == "barracks":
            my_msg = self.barracks

        if stop_loop:
            arcade.stop_sound(self.s)

        self.s = arcade.load_sound(self.soundPath + my_msg)
        arcade.play_sound(self.s)
