
import gobject
import gst
from datetime import datetime, timedelta

from afm import eventmanager
from afm.events import Event

class AudioFailure(Event):
    def __init__(self, source, message):
        self._args = [source, message]
        self.source = source
        self.message = message

class BaseChecker(gobject.GObject):
    warning_emitted = failure_emitted = False
    audio_ok = True

    _tstart = _tend = _texpired = None
    source = gst_element = None

    __gsignals__ = {
        'audio-warning': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                          (str, str, str)),
        'audio-failure': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                          (str, str, str)),
        'audio-ok': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                     (str, str, str)),
        'audio-debug': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                        (str, str, str)),
    }

    def __init__(self, min_tolerance=3000, max_tolerance=7000):
        self.__gobject_init__()
        self.min_tolerance=min_tolerance
        self.max_tolerance=max_tolerance

    def __call__(self):
        return self.gst_element

    def gst_element_factory_make(self, element_name):
        return gst.element_factory_make(
            element_name, '-'.join([element_name,
                                    ''.join(self.source.name.split())])
        )

    def prepare_test(self, source):
        raise NotImplementedError("You must override this method")

    def trigger(self):
        msg = 'Triggered, Warn in %d seconds' % (self.min_tolerance/1000)
        self._tstart = datetime.utcnow()
        self._tend = self._tstart + timedelta(seconds=self.min_tolerance/1000)
        self._texpired = self._tstart + timedelta(seconds=self.max_tolerance/1000)
        eventmanager.emit(AudioFailure(self, msg))
        self.emit('audio-warning', 'WARNING', msg, str(self._tstart))

    @property
    def trigger_active(self):
        return self._tend and self._tend > datetime.utcnow() or False

    @property
    def trigger_expired(self):
        return self._texpired and self._texpired < datetime.utcnow() or False

    def emit_debug(self, message):
        eventmanager.emit(AudioFailure(self, message))
        self.emit('audio-debug', 'DEBUG', message, str(self._tstart))

    def emit_warning(self, message):
        if not self.warning_emitted:
            self.warning_emitted = True
            eventmanager.emit(AudioFailure(self, message))
            self.emit('audio-warning', self.__class__.__name__, message, str(self._tstart))

    def emit_failure(self, message):
        if not self.failure_emitted:
            self.failure_emitted = True
            self.audio_ok = False
            eventmanager.emit(AudioFailure(self, message))
            self.emit('audio-failure', 'FAILURE', message, str(self._tstart))

    def emit_ok(self, message="Trigger Stopped"):
        if not self.audio_ok:
            self.audio_ok = True
            eventmanager.emit(AudioFailure(self, message))
            self.emit('audio-ok', 'OK', message, str(self._tstart))

    def stop_trigger(self, message):
        self.emit_ok(message)
        self.kill_trigger()

    def kill_trigger(self):
        self._tstart = self._tend = None
        self.failure_emitted = self.warning_emitted = False
        self.audio_ok = True

gobject.type_register(BaseChecker)
