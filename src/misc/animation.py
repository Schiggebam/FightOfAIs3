from typing import Union, List

from src.game_accessoires import Army, Drawable
from src.hex_map import HexMap
from src.misc.game_constants import error, hint


class Animator:
    class MoveAnimation:
        def __init__(self, source: (int, int), destination: (int, int), time_ms, drawable: Drawable):
            self.source = source
            self.destination = destination
            self.time_ms = time_ms
            self.start_time_ms = -1
            self.finished = False
            self.drawable = drawable
            self.camera_pos = (0, 0)

        def update(self, time):
            tpl = Animator.bilinear_interpolation(self.source, self.destination, self.start_time_ms,
                                                          self.start_time_ms + self.time_ms, time)
            if len(tpl) != 2:
                error("Animator: serious error, we left the 2d space! len(tpl): " + str(len(tpl)))
                hint(str(self.source))
                hint(str(self.destination))
            self.drawable.set_sprite_pos(tpl, self.camera_pos)

    def __init__(self):
        self.move_animations: List[Animator.MoveAnimation] = []
        self.key_frame_animations: List = []

    def is_active(self):
        return len(self.move_animations) > 0

    def add_move_animation(self, obj: Union[Army], destination: (int, int), time_ms):
        start = HexMap.offset_to_pixel_coords(obj.tile.offset_coordinates)
        dest = HexMap.offset_to_pixel_coords(destination)
        move = Animator.MoveAnimation(start, dest, time_ms, obj)
        self.move_animations.append(move)

    def update(self, time):
        for move in self.move_animations:
            if move.start_time_ms == -1:
                move.start_time_ms = time
            if time > move.start_time_ms + move.time_ms:    #simulation has ended
                move.finished = True
            else:
                move.update(time)

        self.move_animations[:] = [x for x in self.move_animations if not x.finished]

    @staticmethod
    def bilinear_interpolation(a: (int, int), b: (int, int), t_start:float, t_end:float, t:float):
        if t > t_end:
            error("Animator: t > t_end")
        w = (t - t_start) / (t_end - t_start)
        x_pos = a[0] + w * (b[0] - a[0])
        y_pos = a[1] + w * (b[1] - a[1])
        return int(x_pos), int(y_pos)

