"""
gui/effects.py
=================
Small, reusable animation helpers built on QPropertyAnimation and
QGraphicsEffect. QSS alone has no concept of transitions or keyframes,
so anything that actually *moves* over time lives here instead.

Each function attaches its animation object(s) to the widget itself
(e.g. `widget._fade_anim = anim`) so Python doesn't garbage-collect the
animation mid-flight - PySide6 doesn't keep the animation alive on its
own once the local variable that created it goes out of scope.
"""

from __future__ import annotations

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QWidget


def fade_in(widget: QWidget, duration: int = 220) -> QPropertyAnimation:
    """Fade `widget` from transparent to fully opaque. Used on every
    page change so navigating never feels like an abrupt jump-cut."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)

    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    # Graphics effects force indirect (offscreen-buffered) rendering for
    # as long as they're attached, and some effect/grab combinations
    # don't play well together - so once the fade finishes, detach it
    # entirely rather than leaving an always-on "opacity 1.0" effect.
    anim.finished.connect(lambda: widget.setGraphicsEffect(None))
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    widget._fade_anim = anim
    return anim


def pop_in(widget: QWidget, duration: int = 260) -> QPropertyAnimation:
    """A slightly bouncier fade-in for small emphasis moments (feedback
    labels, the bonus round reveal) - distinct from the plain page fade."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)

    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutBack)
    anim.finished.connect(lambda: widget.setGraphicsEffect(None))
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    widget._pop_anim = anim
    return anim


def glow_pulse(
    widget: QWidget,
    color: str = "#E60E2D",
    min_blur: int = 10,
    max_blur: int = 34,
    leg_duration: int = 950,
) -> QSequentialAnimationGroup:
    """A looping soft neon glow, pulsing between `min_blur` and
    `max_blur`. Used on the main menu's hero title for a subtle "always
    alive" feel without being distracting."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setColor(QColor(color))
    effect.setOffset(0, 0)
    effect.setBlurRadius(min_blur)
    widget.setGraphicsEffect(effect)

    grow = QPropertyAnimation(effect, b"blurRadius", widget)
    grow.setDuration(leg_duration)
    grow.setStartValue(min_blur)
    grow.setEndValue(max_blur)
    grow.setEasingCurve(QEasingCurve.Type.InOutSine)

    shrink = QPropertyAnimation(effect, b"blurRadius", widget)
    shrink.setDuration(leg_duration)
    shrink.setStartValue(max_blur)
    shrink.setEndValue(min_blur)
    shrink.setEasingCurve(QEasingCurve.Type.InOutSine)

    group = QSequentialAnimationGroup(widget)
    group.addAnimation(grow)
    group.addAnimation(shrink)
    group.setLoopCount(-1)
    group.start()

    widget._glow_anim_group = group
    return group
