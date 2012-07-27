from numpy import array

from enable.api import KeySpec, BaseTool
from traits.api import Instance
from chaco.tools.api import PanTool, ZoomTool, LineInspector
from chaco.tools.tool_states import PanState
from chaco.api import AbstractOverlay


class PanToolWithHistory(PanTool):
    def __init__(self, *args, **kwargs):
        self.history_tool = kwargs.get('history_tool', None)
        if 'history_tool' in kwargs:
            del kwargs['history_tool']
        super(PanToolWithHistory, self).__init__(*args, **kwargs)

    def _start_pan(self, event, capture_mouse=False):
        super(PanToolWithHistory, self)._start_pan(event, capture_mouse=False)
        if self.history_tool is not None:
            self._start_pan_xy = self._original_xy
            # Save the current data range center so this movement can be
            # undone later.
            self._prev_state = self.history_tool.data_range_center()

    def _end_pan(self, event):
        super(PanToolWithHistory, self)._end_pan(event)
        if self.history_tool is not None:
            # Only append to the undo history if we have moved a significant
            # amount. This avoids conflicts with the single-click undo
            # function.
            new_xy = array((event.x, event.y))
            old_xy = array(self._start_pan_xy)
            if any(abs(new_xy - old_xy) > 10):
                next = self.history_tool.data_range_center()
                prev = self._prev_state
                if next != prev:
                    self.history_tool.append_state(PanState(prev, next))


class KeyboardPanTool(PanToolWithHistory):
    """Allow panning with the keyboard arrow keys"""

    left_key = Instance(KeySpec, args=("Left",))
    right_key = Instance(KeySpec, args=("Right",))
    up_key = Instance(KeySpec, args=("Up",))
    down_key = Instance(KeySpec, args=("Down",))

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
    """Allow the pointer inside the bounds of a plot to be different to the
       pointer outside the bounds."""
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
    def __init__(self, component=None, undo_button='right', *args, **kwargs):
        super(ClickUndoZoomTool, self).__init__(component, *args, **kwargs)
        self.undo_button = undo_button
        self._reverting = False
        self.minimum_undo_delta = 3

    def normal_left_down(self, event):
        """ Handles the left mouse button being pressed while the tool is
        in the 'normal' state.

        If the tool is enabled or always on, it starts selecting.
        """
        if self.undo_button == 'left':
            self._undo_screen_start = (event.x, event.y)
        super(ClickUndoZoomTool, self).normal_left_down(event)

    def normal_right_down(self, event):
        """ Handles the right mouse button being pressed while the tool is
        in the 'normal' state.

        If the tool is enabled or always on, it starts selecting.
        """
        if self.undo_button == 'right':
            self._undo_screen_start = (event.x, event.y)
        super(ClickUndoZoomTool, self).normal_right_down(event)

    def normal_left_up(self, event):
        if self.undo_button == 'left':
            if self._mouse_didnt_move(event):
                self.revert_history()

    def normal_right_up(self, event):
        if self.undo_button == 'right':
            if self._mouse_didnt_move(event):
                self.revert_history()

    def selecting_left_up(self, event):
        self.normal_left_up(event)
        super(ClickUndoZoomTool, self).selecting_left_up(event)

    def selecting_right_up(self, event):
        self.normal_right_up(event)
        super(ClickUndoZoomTool, self).selecting_right_up(event)

    def _mouse_didnt_move(self, event):
        start = array(self._undo_screen_start)
        end = array((event.x, event.y))
        return all(abs(end - start) == 0)

    def clear_undo_history(self):
        self._history_index = 0
        self._history = self._history[:1]

    def revert_history(self):
        if self._history_index > 0:
            self._history_index -= 1
            self._prev_state_pressed()

    def revert_history_all(self):
        self._history_index = 0
        self._reset_state_pressed()

    def _get_mapper_center(self, mapper):
        bounds = mapper.range.low, mapper.range.high
        return bounds[0] + (bounds[1] - bounds[0])/2.

    def data_range_center(self):
        x_center = self._get_mapper_center(self._get_x_mapper())
        y_center = self._get_mapper_center(self._get_y_mapper())
        return x_center, y_center

    def append_state(self, state):
        self._append_state(state, set_index=True)


# Even thought it is an overlay, LineInspector doesn't seem to inherit
# from AbstractOverlay. TraitsTool rightly assumes that it does, so
# double-clicking a plot with a LineInspector overlay causes a traceback.
# https://github.com/enthought/chaco/issues/72
class LineInspectorTool(LineInspector, AbstractOverlay):
    pass
