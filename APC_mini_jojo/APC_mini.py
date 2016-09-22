from __future__ import with_statement
from functools import partial
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ComboElement import ComboElement
from _Framework.Control import ButtonControl
from _Framework.ControlSurface import OptimizedControlSurface
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.Layer import Layer, SimpleLayerOwner
from _Framework.ModesComponent import AddLayerMode, ModesComponent
from _Framework.Resource import SharedResource
from _Framework.SessionComponent import SessionComponent
from _Framework.TransportComponent import TransportComponent
from _Framework.Util import nop
from _APC.APC import APC
from _APC.ControlElementUtils import make_button, make_knob, make_slider
from _APC.DeviceComponent import DeviceComponent
from _APC.MixerComponent import ChanStripComponent as ChanStripComponentBase
from _APC.MixerComponent import MixerComponent as MixerComponentBase
from _APC.SkinDefault import make_default_skin, make_biled_skin, make_stop_button_skin

class SendToggleComponent(ControlSurfaceComponent):
    toggle_control = ButtonControl()

    def __init__(self, mixer, *args, **kwargs):
        super(SendToggleComponent, self).__init__(*args, **kwargs)
        self.mixer = mixer
        self.last_number_of_sends = self.mixer.num_sends
        self.set_toggle_button = self.toggle_control.set_control_element

    def inc_send_index(self):
        if self.mixer.num_sends:
            self.mixer.send_index = (self.mixer.send_index + 1) % self.mixer.num_sends

    @toggle_control.pressed
    def toggle_button_pressed(self, _button):
        self.inc_send_index()


class ChanStripComponent(ChanStripComponentBase):

    def __init__(self, *a, **k):
        self.reset_button_on_exchange = nop
        super(ChanStripComponent, self).__init__(*a, **k)


class MixerComponent(MixerComponentBase):

    def on_num_sends_changed(self):
        if self.send_index is None and self.num_sends > 0:
            self.send_index = 0

    def _create_strip(self):
        return ChanStripComponent()

class APC_mini(APC, OptimizedControlSurface):
    """ phs' hacked Akai APC mini Controller """

    SESSION_WIDTH = 8
    SESSION_HEIGHT = 8
    HAS_TRANSPORT = False

    def make_shifted_button(self, button):
        return ComboElement(button, modifiers=[self._shift_button])

    @classmethod
    def wrap_matrix(cls, control_list, wrapper = nop):
        return ButtonMatrixElement(rows=[map(wrapper, control_list)])

    def __init__(self, *a, **k):
        super(APC_mini, self).__init__(*a, **k)
        self._suppress_session_highlight = False
        self._suppress_send_midi = False
        self._color_skin = make_biled_skin()
        self._default_skin = make_default_skin()
        self._stop_button_skin = make_stop_button_skin()
        with self.component_guard():
            self._create_controls()
            self._session = self._create_session()
            self._mixer = self._create_mixer()
            self._device = self._create_device_component()
            if self.HAS_TRANSPORT:
                self._transport = self._create_transport()
            self.set_device_component(self._device)
            self.set_highlighting_session_component(self._session)
            self._session.set_mixer(self._mixer)
            self._encoder_modes = self._create_encoder_modes()
            self._track_modes = self._create_track_button_modes()
        self._device_selection_follows_track_selection = True
        with self.component_guard():
            self.register_disconnectable(SimpleLayerOwner(layer=Layer(_unused_buttons=self.wrap_matrix(self._unused_buttons))))

    def get_matrix_button(self, column, row):
        return self._matrix_buttons[row][column]

    def _create_controls(self):
        make_on_off_button = partial(make_button, skin=self._default_skin)
        make_color_button = partial(make_button, skin=self._color_skin)
        make_stop_button = partial(make_button, skin=self._stop_button_skin)
        self._shift_button = make_button(0, 98, resource_type=SharedResource, name='Shift_Button')
        self._parameter_knobs = [ make_knob(0, index + 48, name='Parameter_Knob_%d' % (index + 1)) for index in xrange(self.SESSION_WIDTH) ]
        self._select_buttons = [ make_stop_button(0, 64 + index, name='Track_Select_%d' % (index + 1)) for index in xrange(self.SESSION_WIDTH) ]
        self._up_button = self.make_shifted_button(self._select_buttons[0])
        self._down_button = self.make_shifted_button(self._select_buttons[1])
        self._left_button = self.make_shifted_button(self._select_buttons[2])
        self._right_button = self.make_shifted_button(self._select_buttons[3])
        self._volume_button = self.make_shifted_button(self._select_buttons[4])
        self._pan_button = self.make_shifted_button(self._select_buttons[5])
        self._send_button = self.make_shifted_button(self._select_buttons[6])
        self._device_button = self.make_shifted_button(self._select_buttons[7])
        if self.HAS_TRANSPORT:
            self._play_button = make_on_off_button(0, 91, name='Play_Button')
            self._record_button = make_on_off_button(0, 93, name='Record_Button')

        def matrix_note(x, y):
            return x + self.SESSION_WIDTH * (self.SESSION_HEIGHT - y - 1)

        self._matrix_buttons = [ [ make_color_button(0, matrix_note(track, scene), name='%d_Clip_%d_Button' % (track, scene)) for track in xrange(self.SESSION_WIDTH) ] for scene in xrange(self.SESSION_HEIGHT) ]
        self._session_matrix = ButtonMatrixElement(name='Button_Matrix', rows=self._matrix_buttons)
        self._scene_launch_buttons = [ make_color_button(0, index + 82, name='Scene_Launch_%d' % (index + 1)) for index in xrange(self.SESSION_HEIGHT) ]
        self._stop_button = self.make_shifted_button(self._scene_launch_buttons[0])
        self._solo_button = self.make_shifted_button(self._scene_launch_buttons[1])
        self._arm_button = self.make_shifted_button(self._scene_launch_buttons[2])
        self._mute_button = self.make_shifted_button(self._scene_launch_buttons[3])
        self._select_button = self.make_shifted_button(self._scene_launch_buttons[4])
        self._stop_all_button = self._make_stop_all_button()
        self._unused_buttons = map(self.make_shifted_button, self._scene_launch_buttons[5:7])
        self._master_volume_control = make_slider(0, 56, name='Master_Volume')

    def _make_stop_all_button(self):
        return self.make_shifted_button(self._scene_launch_buttons[7])

    def _create_session(self):
        session = SessionComponent(self.SESSION_WIDTH, self.SESSION_HEIGHT, auto_name=True, enable_skinning=True, is_enabled=False, layer=Layer(scene_launch_buttons=self.wrap_matrix(self._scene_launch_buttons), clip_launch_buttons=self._session_matrix, stop_all_clips_button=self._stop_all_button, track_bank_left_button=self._left_button, track_bank_right_button=self._right_button, scene_bank_up_button=self._up_button, scene_bank_down_button=self._down_button))
        for scene_index in xrange(self.SESSION_HEIGHT):
            for track_index in xrange(self.SESSION_WIDTH):
                slot = session.scene(scene_index).clip_slot(track_index)
                slot.layer = Layer(select_button=self._shift_button)

        return session

    def _create_mixer(self):
        mixer = MixerComponent(self.SESSION_WIDTH, auto_name=True, is_enabled=False, invert_mute_feedback=True)
        mixer.master_strip().layer = Layer(volume_control=self._master_volume_control)
        return mixer

    def _create_device_component(self):
        return DeviceComponent(name='Device_Component', is_enabled=False)

    def _create_transport(self):

        def play_toggle_model_transform(value):
            return False if self._shift_button.is_pressed() else value

        return TransportComponent(name='Transport', is_enabled=False, play_toggle_model_transform=play_toggle_model_transform, layer=Layer(play_button=self._play_button, record_button=self._record_button))

    def _create_encoder_modes(self):
        knob_modes = ModesComponent(name='Knob Modes', is_enabled=False)
        parameter_knobs_matrix = self.wrap_matrix(self._parameter_knobs)
        send_toggle_component = SendToggleComponent(self._mixer, name='Toggle Send', is_enabled=False, layer=Layer(toggle_button=self._send_button, priority=1))
        knob_modes.add_mode('volume', AddLayerMode(self._mixer, Layer(volume_controls=parameter_knobs_matrix)))
        knob_modes.add_mode('pan', AddLayerMode(self._mixer, Layer(pan_controls=parameter_knobs_matrix)))
        knob_modes.add_mode('send', [AddLayerMode(self._mixer, Layer(send_controls=parameter_knobs_matrix)), send_toggle_component])
        knob_modes.add_mode('device', AddLayerMode(self._device, Layer(parameter_controls=parameter_knobs_matrix)))
        knob_modes.selected_mode = 'volume'
        knob_modes.layer = Layer(volume_button=self._volume_button, pan_button=self._pan_button, send_button=self._send_button, device_button=self._device_button)
        return knob_modes

    def _create_track_button_modes(self):
        track_button_modes = ModesComponent(name='Track Button Modes', is_enabled=False)
        select_button_matrix = self.wrap_matrix(self._select_buttons)
        track_button_modes.add_mode('clip_stop', AddLayerMode(self._session, Layer(stop_track_clip_buttons=select_button_matrix)))
        track_button_modes.add_mode('solo', AddLayerMode(self._mixer, layer=Layer(solo_buttons=select_button_matrix)))
        track_button_modes.add_mode('arm', AddLayerMode(self._mixer, layer=Layer(arm_buttons=select_button_matrix)))
        track_button_modes.add_mode('mute', AddLayerMode(self._mixer, layer=Layer(mute_buttons=select_button_matrix)))
        track_button_modes.add_mode('select', AddLayerMode(self._mixer, layer=Layer(track_select_buttons=select_button_matrix)))
        track_button_modes.selected_mode = 'clip_stop'
        track_button_modes.layer = Layer(clip_stop_button=self._stop_button, solo_button=self._solo_button, arm_button=self._arm_button, mute_button=self._mute_button, select_button=self._select_button)
        return track_button_modes

    def _enable_components(self):
        with self.component_guard():
            self._session.set_enabled(True)
            self._mixer.set_enabled(True)
            self._device.set_enabled(True)
            if self.HAS_TRANSPORT:
                self._transport.set_enabled(True)
            self._encoder_modes.set_enabled(True)
            self._track_modes.set_enabled(True)

    def _should_combine(self):
        return False

    def _update_hardware(self):
        self._send_midi((240, 126, 127, 6, 1, 247))

    def _product_model_id_byte(self):
        return 40

    def _on_identity_response(self, midi_bytes):
        super(APC_mini, self)._on_identity_response(midi_bytes)
        self._enable_components()

    def _send_dongle_challenge(self):
        pass

    def _on_handshake_successful(self):
        pass
