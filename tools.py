from numpy import array

from enable.api import KeySpec, BaseTool
from traits.api import Instance
from chaco.tools.api import PanTool, ZoomTool, LineInspector
from chaco.api import AbstractOverlay


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


class PointerControlTool(BaseTool):
    def __init__(self, inner_pointer='arrow', *args, **kwargs):
        super(PointerControlTool, self).__init__(*args, **kwargs)
        # self.pointer defined in BaseTool
        self.inner_pointer = inner_pointer

    def normal_mouse_move(self, event):
        def within_bounds(component, x, y):
            if component is None:
                return False
            width, height = component.bounds
            left, top = component.x, component.y
            right, bottom = left + width, top + height
            return x >= left and x <= right and y >= top and y <= bottom

        if event.window:
            if within_bounds(self.component, event.x, event.y):
                # Apparently there's not a better way...
                event.window.set_pointer(self.inner_pointer)
            else:
                event.window.set_pointer(self.pointer)


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


# Even thought it is an overlay, LineInspector doesn't seem to inherit
# from AbstractOverlay. TraitsTool rightly assumes that it does, so
# double-clicking a plot with a LineInspector overlay causes a traceback.
# https://github.com/enthought/chaco/issues/72
class LineInspectorTool(LineInspector, AbstractOverlay):
    pass
