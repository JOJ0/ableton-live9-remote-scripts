from __future__ import with_statement
from functools import partial
from _Framework.ButtonElement import ButtonElement, Color
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ComboElement import ComboElement
from _Framework.Control import ButtonControl
from _Framework.ControlSurface import OptimizedControlSurface
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.InputControlElement import MIDI_NOTE_TYPE, MIDI_CC_TYPE
from _Framework.Layer import Layer, SimpleLayerOwner
from _Framework.ModesComponent import AddLayerMode, ModesComponent
from _Framework.Resource import SharedResource
from _Framework.SessionComponent import SessionComponent
from _Framework.Skin import Skin
from _Framework.SliderElement import SliderElement
from _Framework.TransportComponent import TransportComponent
from _Framework.Util import nop
from _APC.DeviceComponent import DeviceComponent
from _APC.MixerComponent import MixerComponent

from _Framework.DrumRackComponent import DrumRackComponent

UNLIT = Color(0)
GREEN = Color(1)
GREEN_BLINK = Color(2)
RED = Color(3)
RED_BLINK = Color(4)
AMBER = Color(5)
AMBER_BLINK = Color(6)


class Defaults:

    class DefaultButton:
        On = Color(127)
        Off = UNLIT


class BiLedColors:

    class Session:
        ClipStopped = AMBER
        ClipStarted = GREEN
        ClipRecording = RED
        ClipTriggeredPlay = GREEN_BLINK
        ClipTriggeredRecord = RED_BLINK
        ClipEmpty = UNLIT
        Scene = UNLIT
        SceneTriggered = GREEN_BLINK
        NoScene = UNLIT
        StopClip = UNLIT
        StopClipTriggered = GREEN_BLINK
        RecordButton = UNLIT

    class Zooming:
        Selected = AMBER
        Stopped = RED
        Playing = GREEN
        Empty = UNLIT


class StopButtons:

    class Session:
        StopClip = Color(1)
        StopClipTriggered = Color(2)


class SendToggleComponent(ControlSurfaceComponent):
    toggle_control = ButtonControl()

    def __init__(self, mixer, *args, **kwargs):
        super(SendToggleComponent, self).__init__(*args, **kwargs)
        self.mixer = mixer
        self.last_number_of_sends = self.mixer.num_sends
        self.set_toggle_button = self.toggle_control.set_control_element

    def inc_send_index(self):
        if self.mixer.num_sends:
            self.mixer.send_index = \
                (self.mixer.send_index + 1) % self.mixer.num_sends

    @toggle_control.pressed
    def toggle_button_pressed(self, _button):
        self.inc_send_index()


class APC_mini(OptimizedControlSurface):
    """ phs' hacked Akai APC mini Controller """

    def __init__(self, *a, **k):
        super(APC_mini, self).__init__(*a, **k)
        self._suggested_input_port = "Akai APC mini (phs)"
        self._suggested_output_port = "Akai APC mini (phs)"
        self._device_selection_follows_track_selection = True

        with self.component_guard():
            grid_width = 8
            grid_height = 8

            def button(channel, identifier, *a, **k):
                return ButtonElement(True, MIDI_NOTE_TYPE, channel, identifier, *a, **k)

            shift_button = button(0, 98, resource_type=SharedResource)

            def shift(button):
                return ComboElement(button, modifiers=[shift_button])

            def slider(channel, identifier, *a, **k):
                return SliderElement(MIDI_CC_TYPE, channel, identifier, *a, **k)

            on_off_button = partial(button, skin=Skin(Defaults))
            color_button = partial(button, skin=Skin(BiLedColors))
            stop_button = partial(button, skin=Skin(StopButtons))

            sliders = ButtonMatrixElement(
                rows=[[slider(0, i + 48) for i in xrange(grid_width)]])

            select_buttons = [stop_button(0, 64 + i) for i in xrange(grid_width)]
            select_matrix = ButtonMatrixElement(rows=[select_buttons])

            up_button = shift(select_buttons[0])
            down_button = shift(select_buttons[1])
            left_button = shift(select_buttons[2])
            right_button = shift(select_buttons[3])
            volume_button = shift(select_buttons[4])
            pan_button = shift(select_buttons[5])
            send_button = shift(select_buttons[6])
            device_button = shift(select_buttons[7])

            grid_buttons = [[
                color_button(0, x + grid_width * (grid_height - y - 1))
                for x in xrange(grid_width)]
                for y in xrange(grid_height)]

            grid_matrix = ButtonMatrixElement(rows=grid_buttons)

            scene_buttons = [color_button(0, i + 82) for i in xrange(grid_height)]
            scene_matrix = ButtonMatrixElement(rows=[scene_buttons])

            stop_button = shift(scene_buttons[0])
            solo_button = shift(scene_buttons[1])
            arm_button = shift(scene_buttons[2])
            mute_button = shift(scene_buttons[3])
            select_button = shift(scene_buttons[4])
            notes_button = shift(scene_buttons[5])
            stop_all_button = shift(scene_buttons[7])
            unused_buttons = ButtonMatrixElement(rows=[[shift(scene_buttons[6])]])

            master_volume = slider(0, 56)

            session = SessionComponent(
                grid_width,
                grid_height,
                auto_name=True,
                enable_skinning=True,
                is_enabled=False,
                layer=Layer(
                    scene_launch_buttons=scene_matrix,
                    clip_launch_buttons=grid_matrix,
                    stop_all_clips_button=stop_all_button,
                    track_bank_left_button=left_button,
                    track_bank_right_button=right_button,
                    scene_bank_up_button=up_button,
                    scene_bank_down_button=down_button))

            for scene_index in xrange(grid_height):
                for track_index in xrange(grid_width):
                    slot = session.scene(scene_index).clip_slot(track_index)
                    slot.layer = Layer(select_button=shift_button)

            self.set_highlighting_session_component(session)

            mixer = MixerComponent(
                grid_width,
                auto_name=True,
                is_enabled=False,
                invert_mute_feedback=True)

            mixer.master_strip().layer = Layer(volume_control=master_volume)
            session.set_mixer(mixer)

            device = DeviceComponent(is_enabled=False)
            self.set_device_component(device)

            has_transport = False
            if has_transport:
                play_button = on_off_button(0, 91)
                record_button = on_off_button(0, 93)

                def play_toggle_model_transform(value):
                    return False if shift_button.is_pressed() else value

                transport = TransportComponent(
                    is_enabled=False,
                    play_toggle_model_transform=play_toggle_model_transform,
                    layer=Layer(
                        play_button=play_button,
                        record_button=record_button))

            def layer_mode(component, **kwargs):
                return AddLayerMode(component, layer=Layer(**kwargs))

            send_toggle_component = SendToggleComponent(
                mixer,
                is_enabled=False,
                layer=Layer(toggle_button=send_button, priority=1))

            volume_mode = layer_mode(mixer, volume_controls=sliders)
            pan_mode = layer_mode(mixer, pan_controls=sliders)
            send_mode = layer_mode(mixer, send_controls=sliders)
            device_mode = layer_mode(device, parameter_controls=sliders)

            slider_modes = ModesComponent(is_enabled=False)
            slider_modes.add_mode('volume', volume_mode)
            slider_modes.add_mode('pan', pan_mode)
            slider_modes.add_mode('send', [send_mode, send_toggle_component])
            slider_modes.add_mode('device', device_mode)
            slider_modes.selected_mode = 'volume'
            slider_modes.layer = Layer(
                volume_button=volume_button,
                pan_button=pan_button,
                send_button=send_button,
                device_button=device_button)

            drum_pads = ButtonMatrixElement(
                rows=[
                    grid_buttons[0][0:4],
                    grid_buttons[1][0:4],
                    grid_buttons[2][0:4],
                    grid_buttons[3][0:4]])

            drum_rack = DrumRackComponent(is_enabled=True)

            stop_track_mode = layer_mode(session, stop_track_clip_buttons=select_matrix)
            solo_mode = layer_mode(mixer, solo_buttons=select_matrix)
            arm_mode = layer_mode(mixer, arm_buttons=select_matrix)
            mute_mode = layer_mode(mixer, mute_buttons=select_matrix)
            select_mode = layer_mode(mixer, track_select_buttons=select_matrix)
            drum_mode = layer_mode(drum_rack, pads=drum_pads)

            track_modes = ModesComponent(is_enabled=False)
            track_modes.add_mode('clip_stop', stop_track_mode)
            track_modes.add_mode('solo', solo_mode)
            track_modes.add_mode('arm', arm_mode)
            track_modes.add_mode('mute', mute_mode)
            track_modes.add_mode('select', select_mode)
            track_modes.add_mode('notes', drum_mode)
            track_modes.selected_mode = 'clip_stop'
            track_modes.layer = Layer(
                clip_stop_button=stop_button,
                solo_button=solo_button,
                arm_button=arm_button,
                mute_button=mute_button,
                select_button=select_button,
                notes_button=notes_button)

            self.register_disconnectable(SimpleLayerOwner(
                layer=Layer(_unused_buttons=unused_buttons)))

            self._disabled_during_handshake =[
                session,
                mixer,
                device,
                # transport,
                slider_modes,
                track_modes]

    def refresh_state(self):
        super(APC_mini, self).refresh_state()

        with self.component_guard():
            for component in self._disabled_during_handshake:
                component.set_enabled(False)

        self.schedule_message(5, self._send_identity_request)

    def _send_identity_request(self):
        self._send_midi((240, 126, 127, 6, 1, 247))

    def handle_sysex(self, midi_bytes):
        if midi_bytes[3] == 6 and midi_bytes[4] == 2:
            with self.component_guard():
                for component in self._disabled_during_handshake:
                    component.set_enabled(True)
