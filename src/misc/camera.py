from typing import Tuple, List, Any, Callable

from src.misc.game_constants import CAMERA_SENSITIVITY


class Camera:
    """Simple class, which controls the viewport of the screen
    This class is not threat safe"""
    def __init__(self, screen_width, screen_height):
        self.__position: Tuple[int, int] = (0, 0)
        self.screen_height = screen_height
        self.screen_width = screen_width

        self.rel_x = 0
        self.rel_y = 0
        self.camera_has_moved = False
        self._camera_event_listener: List[Tuple[Any, Callable[[Tuple[int, int], Tuple[int, int]], None]]] = []
        self.up_key = False
        self.down_key = False
        self.left_key = False
        self.right_key = False

    def get_position(self) -> Tuple[int, int]:
        """get the camera position: this is the lower left corner"""
        return self.__position

    def set_position(self, pos: Tuple[int, int]):
        """set the offset of the lower left corner of the screen in pixels"""
        self.__position = pos

    def set_center(self, center: Tuple[int, int]):
        """set the focus point of the camera (center) on a specific pixel offset"""
        tmp_x = center[0] - self.screen_width / 2
        tmp_y = center[1] - self.screen_height / 2
        self.__position = (tmp_x, tmp_y)

    def register(self, obj: Any, callback: Callable[[Tuple[int, int], Tuple[int, int]], None]):
        """if an objects wants to get notified upon movement, it can register with an reference to itself and
        a callback function which deals with the relative and absolute camera movement"""
        self._camera_event_listener.append((obj, callback))

    def update(self, delta_t: float):
        rel = int(float(CAMERA_SENSITIVITY) * delta_t)
        if self.up_key:
            self.camera_has_moved = True
            self.rel_y = - rel
            self.__position = (self.__position[0], self.__position[1] + self.rel_y)
        elif self.down_key:
            self.camera_has_moved = True
            self.rel_y = rel
            self.__position = (self.__position[0], self.__position[1] + self.rel_y)
        if self.left_key:
            self.camera_has_moved = True
            self.rel_x = rel
            self.__position = (self.__position[0] + self.rel_x, self.__position[1])
        elif self.right_key:
            self.camera_has_moved = True
            self.rel_x = - rel
            self.__position = (self.__position[0] + self.rel_x, self.__position[1])

        if self.camera_has_moved:
            for obj, call in self._camera_event_listener:
                obj.call((self.rel_x, self.rel_y), self.__position)

            # for s_list in self.z_levels:
            #     for sp in s_list:
            #         sp.center_x = sp.center_x + self.rel_x
            #         sp.center_y = sp.center_y + self.rel_y
            # self.gl.set_camera_pos(self.camera_x, self.camera_y)
            # self.gl.animator.update_camera_pos((self.camera_x, self.camera_y))
            # #self.gl.animator.camera_pos = (self.camera_x, self.camera_y)
            # self.ui.camera_pos = (self.camera_x, self.camera_y)
            # for listener in self.camera_event_listener:
            #     listener.camera_pos = (self.camera_x, self.camera_y)
            self.camera_has_moved = False
            self.rel_x = 0
            self.rel_y = 0
