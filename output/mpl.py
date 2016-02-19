#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#------------------------------------------------------------------------------
""" Chaco's SVG backend

    :Copyright:   ActiveState
    :License:     BSD Style
    :Author:      David Ascher (davida@activestate.com)
    :Version:     $Revision: 1.5 $
"""

# Major library imports
from cStringIO import StringIO
from numpy import array, pi
import warnings

# Local, relative Kiva imports
from kiva import affine
from kiva import basecore2d
from kiva import constants
from kiva.constants import FILL, FILL_STROKE, EOF_FILL_STROKE, EOF_FILL, STROKE
from kiva import agg


from matplotlib.font_manager import FontProperties
from matplotlib.path import Path
from matplotlib.transforms import Affine2D, TransformedPath

line_cap_map = {
    constants.CAP_ROUND: 'round',
    constants.CAP_SQUARE: 'projecting',
    constants.CAP_BUTT: 'butt'
    }

line_join_map = {
    constants.JOIN_ROUND: 'round',
    constants.JOIN_BEVEL: 'bevel',
    constants.JOIN_MITER: 'miter'
    }


font_face_map = {'Arial': 'Helvetica'}

class CompiledPath(object):
    pass

import matplotlib as mpl

#mpl.rcParams['text.usetex'] = True
#mpl.rcParams['text.latex.unicode'] = True
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['mathtext.default'] = 'regular'

def is_subscript(code):
    return code >= 0x2080 and code < 0x2090

def escape_unicode_as_mathtext(string, i):
    ch = string[i]
    code = ord(ch)
    if code > 128:
        j = i + 1
        # This is dumb.
        if is_subscript(code):
            while is_subscript(ord(string[j])) and j < len(string):
                j += 1
            output = u'_{' + u''.join(map(lambda c: str(ord(c) - 0x2080), string[i:j])) + u'}'
        else:
            output = ch
        return u''.join([ u'$', output, u'$' ]), j
    return ch, i + 1

def unicode_to_mathtext(string):
    new_string = u''
    strlen = len(string)
    i = 0
    while i < strlen:
        new, i = escape_unicode_as_mathtext(string, i)
        new_string += new
    return new_string


class GraphicsContext(basecore2d.GraphicsContextBase):

    def __init__(self, size, dpi=72, format='png', renderer=None, *args, **kwargs):
        super(GraphicsContext, self).__init__(self, size, *args, **kwargs)
        width, height = size
        self.size = size
        self._height = height
        self.contents = StringIO()
        self._clipmap = {}
        self.format = format
        self._font_prop = FontProperties(weight='roman')
        self.state._transformed_clip_path = None
        import matplotlib.pyplot as plt
        self.figure = plt.figure()
        self._backend = renderer

    def render(self, format):
        return self.contents.getvalue()

    def clear(self):
        # TODO: clear the contents
        pass

    def width(self):
        return self.size[0]

    def height(self):
        return self.size[1]

    def save(self, filename):
        f = open(filename, 'w')
        self._backend.finalize()
        f.write(self.contents.getvalue())
        f.close()

    # Text handling code

    def set_font(self, font):
        import kiva.constants as kc

        # Mapping of strings to valid Kiva font families:
        font_families = {
            kc.DEFAULT: 'default',
            kc.DECORATIVE: 'decorative',
            kc.ROMAN: 'rm',
            kc.SCRIPT: 'script',
            kc.SWISS: 'swiss',
            kc.MODERN: 'cm',
        }

        self.state.font = font
        face_name = font.face_name
        if face_name == '':
            face_name = 'Bitstream Vera Sans'
        else:
            face_name = font_families[font.family]
        self._font_prop.set_size(font.size)
        self._font_prop.set_weight('bold' if font.weight else 'regular')
        self._font_prop.set_family(face_name)

    def device_show_text(self, text):
        ttm = self.get_text_matrix()
        ctm = self.get_ctm()  # not device_ctm!!
        m = affine.concat(ctm,ttm)
        tx,ty,sx,sy,angle = affine.trs_factor(m)
        angle = angle * 180. / pi
        gc = self._backend.new_gc()
        text = unicode_to_mathtext(text)
        if self._backend.flipy():
            ty = self.height() - ty
        self._backend.draw_text(gc, tx, ty - 1, text,
                                self._font_prop, angle, ismath=True)
        gc.restore()

    def device_get_full_text_extent(self, text):
        text = unicode_to_mathtext(text)
        width, height, descent = self._backend.get_text_width_height_descent(text, self._font_prop, ismath=True)
        return width, height, descent, 0. #height*1.2 # assume leading of 1.2*height

    # actual implementation =)

    def device_draw_image(self, img, rect):
        """
        draw_image(img_gc, rect=(x,y,w,h))

        Draws another gc into this one.  If 'rect' is not provided, then
        the image gc is drawn into this one, rooted at (0,0) and at full
        pixel size.  If 'rect' is provided, then the image is resized
        into the (w,h) given and drawn into this GC at point (x,y).

        img_gc is either a Numeric array (WxHx3 or WxHx4) or a GC from Kiva's
        Agg backend (kiva.agg.GraphicsContextArray).

        Requires the Python Imaging Library (PIL).
        """
        from PIL import Image as PilImage
        from matplotlib import _image

        # We turn img into a PIL object, since that is what ReportLab
        # requires.  To do this, we first determine if the input image
        # GC needs to be converted to RGBA/RGB.  If so, we see if we can
        # do it nicely (using convert_pixel_format), and if not, we do
        # it brute-force using Agg.
        if type(img) == type(array([])):
            # Numeric array
            converted_img = agg.GraphicsContextArray(img, pix_format='rgba32')
            format = 'RGBA'
        elif isinstance(img, agg.GraphicsContextArray):
            if img.format().startswith('RGBA'):
                format = 'RGBA'
            elif img.format().startswith('RGB'):
                format = 'RGB'
            else:
                converted_img = img.convert_pixel_format('rgba32', inplace=0)
                format = 'RGBA'
            # Should probably take this into account
            # interp = img.get_image_interpolation()
        else:
            warnings.warn("Cannot render image of type %r into SVG context."
                          % type(img))
            return

        if rect == None:
            rect = (0, 0, img.width(), img.height())

        width, height = img.width(), img.height()

        # converted_img now holds an Agg graphics context with the image
        pil_img = PilImage.fromstring(format,
                                      (converted_img.width(),
                                       converted_img.height()),
                                      converted_img.bmp_array.tostring())

        left, top, width, height = rect
        if width != img.width() or height != img.height():
            # This is not strictly required.
            pil_img = pil_img.resize((int(width), int(height)), PilImage.NEAREST)
        pil_img = pil_img.transpose(PilImage.FLIP_TOP_BOTTOM)
        # Fix for the SVG backend, which seems to flip x when a transform is provided.
        if self._backend.flipy():
            pil_img = pil_img.transpose(PilImage.FLIP_LEFT_RIGHT)

        mpl_img = _image.frombuffer(pil_img.tostring(), width, height, True)
        mpl_img.is_grayscale = False

        gc = self._backend.new_gc()
        if self.state.clipping_path:
            gc.set_clip_path(self._get_transformed_clip_path())
        transform = Affine2D.from_values(*affine.affine_params(self.get_ctm()))
        self._backend.draw_image(gc, left, top, mpl_img,
                                 dx=width, dy=height, transform=transform)
        gc.restore()

    def device_fill_points(self, points, mode):
        if mode in (FILL, FILL_STROKE, EOF_FILL_STROKE, EOF_FILL):
            fill = tuple(self.state.fill_color)
        else:
            fill = None
        if mode in (STROKE, FILL_STROKE, EOF_FILL_STROKE):
            color = tuple(self.state.line_color)
        else:
            color = tuple(self.state.fill_color)
        path = Path(points)
        gc = self._backend.new_gc()
        gc.set_linewidth(self.state.line_width)
        if not (self.state.line_dash[1] == 0).all():
            gc.set_dashes(self.state.line_dash[0], list(self.state.line_dash[1]))
        if self.state.clipping_path:
            gc.set_clip_path(self._get_transformed_clip_path())
        gc.set_joinstyle(line_join_map[self.state.line_join])
        gc.set_capstyle(line_cap_map[self.state.line_cap])
        gc.set_foreground(color, isRGBA=True)
        gc.set_alpha(self.state.alpha)
        transform = Affine2D.from_values(*affine.affine_params(self.get_ctm()))
        self._backend.draw_path(gc, path, transform, fill)
        gc.restore()

    def _get_transformed_clip_path(self):
        x, y, width, height = self.state.clipping_path
        rect = ((x, y), (x+width, y), (x+width, y+height), (x, y+height))
        transform = Affine2D.from_values(*affine.affine_params(self.get_ctm()))
        return TransformedPath(Path(rect), transform)

    # noops which seem to be needed

    def device_stroke_points(self, points, mode):
        # handled by device_fill_points
        pass

    def device_set_clipping_path(self, x, y, width, height):
        pass

    def device_destroy_clipping_path(self):
        pass

    def device_update_line_state(self):
        pass

    def device_update_fill_state(self):
        pass


def font_metrics_provider():
    return GraphicsContext((1,1))

