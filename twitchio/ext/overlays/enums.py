"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from enum import Enum


__all__ = ("Alignment", "Animation", "AnimationSpeed", "Font")


class Animation(Enum):
    """...

    Attributes
    ----------
    bounce: :class:`str`
        The "bounce" class in Animate.css.
    flash: :class:`str`
        The "flash" class in Animate.css.
    pulse: :class:`str`
        The "pulse" class in Animate.css.
    rubber_band: :class:`str`
        The "RubberBand" class in Animate.css.
    shake_x: :class:`str`
        The "ShakeX" class in Animate.css.
    shake_y: :class:`str`
        The "ShakeY" class in Animate.css.
    head_shake: :class:`str`
        The "HeadShake" class in Animate.css.
    swing: :class:`str`
        The "swing" class in Animate.css.
    tada: :class:`str`
        The "tada" class in Animate.css.
    wobble: :class:`str`
        The "wobble" class in Animate.css.
    jello: :class:`str`
        The "jello" class in Animate.css.
    heart_beat: :class:`str`
        The "HeartBeat" class in Animate.css.
    back_in_down: :class:`str`
        The "BackInDown" class in Animate.css.
    back_in_left: :class:`str`
        The "BackInLeft" class in Animate.css.
    back_in_right: :class:`str`
        The "BackInRight" class in Animate.css.
    back_in_up: :class:`str`
        The "BackInUp" class in Animate.css.
    back_out_down: :class:`str`
        The "BackOutDown" class in Animate.css.
    back_out_left: :class:`str`
        The "BackOutLeft" class in Animate.css.
    back_out_right: :class:`str`
        The "BackOutRight" class in Animate.css.
    back_out_up: :class:`str`
        The "BackOutUp" class in Animate.css.
    bounce_in: :class:`str`
        The "BounceIn" class in Animate.css.
    bounce_in_down: :class:`str`
        The "BounceInDown" class in Animate.css.
    bounce_in_left: :class:`str`
        The "BounceInLeft" class in Animate.css.
    bounce_in_right: :class:`str`
        The "BounceInRight" class in Animate.css.
    bounce_in_up: :class:`str`
        The "BounceInUp" class in Animate.css.
    bounce_out: :class:`str`
        The "BounceOut" class in Animate.css.
    bounce_out_down: :class:`str`
        The "BounceOutDown" class in Animate.css.
    bounce_out_left: :class:`str`
        The "BounceOutLeft" class in Animate.css.
    bounce_out_right: :class:`str`
        The "BounceOutRight" class in Animate.css.
    bounce_out_up: :class:`str`
        The "BounceOutUp" class in Animate.css.
    fade_in: :class:`str`
        The "FadeIn" class in Animate.css.
    fade_in_down: :class:`str`
        The "FadeInDown" class in Animate.css.
    fade_in_down_big: :class:`str`
        The "FadeInDownBig" class in Animate.css.
    fade_in_left: :class:`str`
        The "FadeInLeft" class in Animate.css.
    fade_in_left_big: :class:`str`
        The "FadeInLeftBig" class in Animate.css.
    fade_in_right: :class:`str`
        The "FadeInRight" class in Animate.css.
    fade_in_right_big: :class:`str`
        The "FadeInRightBig" class in Animate.css.
    fade_in_up: :class:`str`
        The "FadeInUp" class in Animate.css.
    fade_in_up_big: :class:`str`
        The "FadeInUpBig" class in Animate.css.
    fade_in_top_left: :class:`str`
        The "FadeInTopLeft" class in Animate.css.
    fade_in_top_right: :class:`str`
        The "FadeInTopRight" class in Animate.css.
    fade_in_bottom_left: :class:`str`
        The "FadeInBottomLeft" class in Animate.css.
    fade_in_bottom_right: :class:`str`
        The "FadeInBottomRight" class in Animate.css.
    fade_out: :class:`str`
        The "FadeOut" class in Animate.css.
    fade_out_down: :class:`str`
        The "FadeOutDown" class in Animate.css.
    fade_out_down_big: :class:`str`
        The "FadeOutDownBig" class in Animate.css.
    fade_out_left: :class:`str`
        The "FadeOutLeft" class in Animate.css.
    fade_out_left_big: :class:`str`
        The "FadeOutLeftBig" class in Animate.css.
    fade_out_right: :class:`str`
        The "FadeOutRight" class in Animate.css.
    fade_out_right_big: :class:`str`
        The "FadeOutRightBig" class in Animate.css.
    fade_out_up: :class:`str`
        The "FadeOutUp" class in Animate.css.
    fade_out_up_big: :class:`str`
        The "FadeOutUpBig" class in Animate.css.
    fade_out_top_left: :class:`str`
        The "FadeOutTopLeft" class in Animate.css.
    fade_out_top_right: :class:`str`
        The "FadeOutTopRight" class in Animate.css.
    fade_out_bottom_right: :class:`str`
        The "FadeOutBottomRight" class in Animate.css.
    fade_out_bottom_left: :class:`str`
        The "FadeOutBottomLeft" class in Animate.css.
    flip: :class:`str`
        The "flip" class in Animate.css.
    flip_in_x: :class:`str`
        The "FlipInX" class in Animate.css.
    flip_in_y: :class:`str`
        The "FlipInY" class in Animate.css.
    flip_out_x: :class:`str`
        The "FlipOutX" class in Animate.css.
    flip_out_y: :class:`str`
        The "FlipOutY" class in Animate.css.
    light_speed_in_right: :class:`str`
        The "LightSpeedInRight" class in Animate.css.
    light_speed_in_left: :class:`str`
        The "LightSpeedInLeft" class in Animate.css.
    light_speed_out_right: :class:`str`
        The "LightSpeedOutRight" class in Animate.css.
    light_speed_out_left: :class:`str`
        The "LightSpeedOutLeft" class in Animate.css.
    rotate_in: :class:`str`
        The "RotateIn" class in Animate.css.
    rotate_in_down_left: :class:`str`
        The "RotateInDownLeft" class in Animate.css.
    rotate_in_down_right: :class:`str`
        The "RotateInDownRight" class in Animate.css.
    rotate_in_up_left: :class:`str`
        The "RotateInUpLeft" class in Animate.css.
    rotate_in_up_right: :class:`str`
        The "RotateInUpRight" class in Animate.css.
    rotate_out: :class:`str`
        The "RotateOut" class in Animate.css.
    rotate_out_down_left: :class:`str`
        The "RotateOutDownLeft" class in Animate.css.
    rotate_out_down_right: :class:`str`
        The "RotateOutDownRight" class in Animate.css.
    rotate_out_up_left: :class:`str`
        The "RotateOutUpLeft" class in Animate.css.
    rotate_out_up_right: :class:`str`
        The "RotateOutUpRight" class in Animate.css.
    hinge: :class:`str`
        The "hinge" class in Animate.css.
    jack_in_the_box: :class:`str`
        The "JackInTheBox" class in Animate.css.
    roll_in: :class:`str`
        The "RollIn" class in Animate.css.
    roll_out: :class:`str`
        The "RollOut" class in Animate.css.
    zoom_in: :class:`str`
        The "ZoomIn" class in Animate.css.
    zoom_in_down: :class:`str`
        The "ZoomInDown" class in Animate.css.
    zoom_in_left: :class:`str`
        The "ZoomInLeft" class in Animate.css.
    zoom_in_right: :class:`str`
        The "ZoomInRight" class in Animate.css.
    zoom_in_up: :class:`str`
        The "ZoomInUp" class in Animate.css.
    zoom_out: :class:`str`
        The "ZoomOut" class in Animate.css.
    zoom_out_down: :class:`str`
        The "ZoomOutDown" class in Animate.css.
    zoom_out_left: :class:`str`
        The "ZoomOutLeft" class in Animate.css.
    zoom_out_right: :class:`str`
        The "ZoomOutRight" class in Animate.css.
    zoom_out_up: :class:`str`
        The "ZoomOutUp" class in Animate.css.
    slide_in_down: :class:`str`
        The "SlideInDown" class in Animate.css.
    slide_in_left: :class:`str`
        The "SlideInLeft" class in Animate.css.
    slide_in_right: :class:`str`
        The "SlideInRight" class in Animate.css.
    slide_in_up: :class:`str`
        The "SlideInUp" class in Animate.css.
    slide_out_down: :class:`str`
        The "SlideOutDown" class in Animate.css.
    slide_out_left: :class:`str`
        The "SlideOutLeft" class in Animate.css.
    slide_out_right: :class:`str`
        The "SlideOutRight" class in Animate.css.
    slide_out_up: :class:`str`
        The "SlideOutUp" class in Animate.css.
    """

    bounce = "bounce"
    flash = "flash"
    pulse = "pulse"
    rubber_band = "rubberBand"
    shake_x = "shakeX"
    shake_y = "shakeY"
    head_shake = "headShake"
    swing = "swing"
    tada = "tada"
    wobble = "wobble"
    jello = "jello"
    heart_beat = "heartBeat"
    back_in_down = "backInDown"
    back_in_left = "backInLeft"
    back_in_right = "backInRight"
    back_in_up = "backInUp"
    back_out_down = "backOutDown"
    back_out_left = "backOutLeft"
    back_out_right = "backOutRight"
    back_out_up = "backOutUp"
    bounce_in = "bounceIn"
    bounce_in_down = "bounceInDown"
    bounce_in_left = "bounceInLeft"
    bounce_in_right = "bounceInRight"
    bounce_in_up = "bounceInUp"
    bounce_out = "bounceOut"
    bounce_out_down = "bounceOutDown"
    bounce_out_left = "bounceOutLeft"
    bounce_out_right = "bounceOutRight"
    bounce_out_up = "bounceOutUp"
    fade_in = "fadeIn"
    fade_in_down = "fadeInDown"
    fade_in_down_big = "fadeInDownBig"
    fade_in_left = "fadeInLeft"
    fade_in_left_big = "fadeInLeftBig"
    fade_in_right = "fadeInRight"
    fade_in_right_big = "fadeInRightBig"
    fade_in_up = "fadeInUp"
    fade_in_up_big = "fadeInUpBig"
    fade_in_top_left = "fadeInTopLeft"
    fade_in_top_right = "fadeInTopRight"
    fade_in_bottom_left = "fadeInBottomLeft"
    fade_in_bottom_right = "fadeInBottomRight"
    fade_out = "fadeOut"
    fade_out_down = "fadeOutDown"
    fade_out_down_big = "fadeOutDownBig"
    fade_out_left = "fadeOutLeft"
    fade_out_left_big = "fadeOutLeftBig"
    fade_out_right = "fadeOutRight"
    fade_out_right_big = "fadeOutRightBig"
    fade_out_up = "fadeOutUp"
    fade_out_up_big = "fadeOutUpBig"
    fade_out_top_left = "fadeOutTopLeft"
    fade_out_top_right = "fadeOutTopRight"
    fade_out_bottom_right = "fadeOutBottomRight"
    fade_out_bottom_left = "fadeOutBottomLeft"
    flip = "flip"
    flip_in_x = "flipInX"
    flip_in_y = "flipInY"
    flip_out_x = "flipOutX"
    flip_out_y = "flipOutY"
    light_speed_in_right = "lightSpeedInRight"
    light_speed_in_left = "lightSpeedInLeft"
    light_speed_out_right = "lightSpeedOutRight"
    light_speed_out_left = "lightSpeedOutLeft"
    rotate_in = "rotateIn"
    rotate_in_down_left = "rotateInDownLeft"
    rotate_in_down_right = "rotateInDownRight"
    rotate_in_up_left = "rotateInUpLeft"
    rotate_in_up_right = "rotateInUpRight"
    rotate_out = "rotateOut"
    rotate_out_down_left = "rotateOutDownLeft"
    rotate_out_down_right = "rotateOutDownRight"
    rotate_out_up_left = "rotateOutUpLeft"
    rotate_out_up_right = "rotateOutUpRight"
    hinge = "hinge"
    jack_in_the_box = "jackInTheBox"
    roll_in = "rollIn"
    roll_out = "rollOut"
    zoom_in = "zoomIn"
    zoom_in_down = "zoomInDown"
    zoom_in_left = "zoomInLeft"
    zoom_in_right = "zoomInRight"
    zoom_in_up = "zoomInUp"
    zoom_out = "zoomOut"
    zoom_out_down = "zoomOutDown"
    zoom_out_left = "zoomOutLeft"
    zoom_out_right = "zoomOutRight"
    zoom_out_up = "zoomOutUp"
    slide_in_down = "slideInDown"
    slide_in_left = "slideInLeft"
    slide_in_right = "slideInRight"
    slide_in_up = "slideInUp"
    slide_out_down = "slideOutDown"
    slide_out_left = "slideOutLeft"
    slide_out_right = "slideOutRight"
    slide_out_up = "slideOutUp"


class Font(Enum): ...


class AnimationSpeed(Enum):
    default = None
    slow = "slow"
    slower = "slower"
    fast = "fast"
    faster = "faster"


class EventPosition(Enum):
    top_left = "tl"
    top_center = "tc"
    top_right = "tr"
    center_left = "cl"
    center = "cc"
    center_right = "cr"
    bottom_left = "bl"
    bottom_center = "bc"
    bottom_right = "br"


class Alignment(Enum):
    left = "s"
    center = "c"
    right = "e"
