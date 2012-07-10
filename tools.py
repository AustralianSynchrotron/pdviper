from numpy import array

from enable.api import KeySpec
from traits.api import Instance
from chaco.tools.api import PanTool, ZoomTool


class KeyboardPanTool(PanTool):
    left_key = Instance(KeySpec, args=("Left",))
    right_key = Instance(KeySpec, args=("Right",))
    up_key = Instance(KeySpec, args=("Up",))
    down_key = Instance(KeySpec, args=("Down",))

    def __init__(self, *args, **kwargs):
        super(KeyboardPanTool, self).__init__(*args, **kwargs)

    def normal_key_pressed(self, event):
        x, y = (0, 0)
        pan_amount = 40
        if self.left_key.match(event):
            x += pan_amount
        elif self.right_key.match(event):
            x -= pan_amount
        elif self.up_key.match(event):
            y -= pan_amount
        elif self.down_key.match(event):
            y += pan_amount

        if x or y:
            self._start_pan(event)
            (event.x, event.y) = (self._original_xy[0] + x, self._original_xy[1] + y)
            self.panning_mouse_move(event)
            self._end_pan(event)

    def normal_mouse_move(self, event):
        if event.window:
            # Apparently there's not a better way...
            event.window.set_pointer("cross")


class ClickUndoZoomTool(ZoomTool):
    def _pop_state_on_single_click(self, event):
        self._screen_end = (event.x, event.y)
        start = array(self._screen_start)
        end = array(self._screen_end)
        if sum(abs(end - start)) < self.minimum_screen_delta:
            if self._history_index > 0:
                self._history_index -= 1
                self._prev_state_pressed()

    def selecting_left_up(self, event):
        """ Handles the left mouse button being released when the tool is in
        the 'selecting' state.

        Finishes selecting and does the zoom.
        """
        if self.drag_button == "left":
            self._pop_state_on_single_click(event)
            self._end_select(event)
        return

    def selecting_right_up(self, event):
        """ Handles the right mouse button being released when the tool is in
        the 'selecting' state.

        Finishes selecting and does the zoom.
        """
        if self.drag_button == "right":
            self._pop_state_on_single_click(event)
            self._end_select(event)
        return

    def clear_undo_history(self):
        self._history_index = 0
        self._history = self._history[:1]

