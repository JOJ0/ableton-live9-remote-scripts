from __future__ import with_statement
from functools import partial
from _Framework.ButtonElement import ButtonElement, Color
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ComboElement import ComboElement
from _Framework.CompoundComponent import CompoundComponent
from _Framework.Control import ButtonControl, RadioButtonGroup
from _Framework.ControlSurface import OptimizedControlSurface
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.Dependency import depends
from _Framework.InputControlElement import MIDI_NOTE_TYPE, MIDI_CC_TYPE
from _Framework.Layer import Layer, SimpleLayerOwner
from _Framework.ModesComponent import AddLayerMode, ModesComponent
from _Framework.Resource import SharedResource
from _Framework.ScrollComponent import ScrollComponent
from _Framework.Skin import Skin
from _Framework.SliderElement import SliderElement
from _Framework.TransportComponent import TransportComponent
from _Framework.Util import nop
from _APC.DeviceComponent import DeviceComponent
from _APC.MixerComponent import MixerComponent
from Push.SpecialSessionComponent import SpecialSessionComponent


OFF = Color(0)
ON = Color(127)
GREEN = Color(1)
GREEN_BLINK = Color(2)
RED = Color(3)
RED_BLINK = Color(4)
AMBER = Color(5)
AMBER_BLINK = Color(6)

NON_FEEDBACK_CHANNEL = 0
ALL_FEEDBACK_CHANNELS = xrange(1, 16)
PIANO_FEEDBACK_CHANNELS = xrange(1, 12)
DRUM_KIT_FEEDBACK_CHANNELS = xrange(12, 16)


class Colors:

    class Session:
        ClipStopped = AMBER
        ClipStarted = GREEN
        ClipRecording = RED
        ClipTriggeredPlay = GREEN_BLINK
        ClipTriggeredRecord = RED_BLINK
        ClipEmpty = OFF
        Scene = OFF
        SceneTriggered = GREEN_BLINK
        NoScene = OFF
        StopClip = OFF
        StopClipTriggered = GREEN_BLINK
        RecordButton = OFF

    class Piano:
        NoteBase = GREEN
        NoteLit = AMBER
        NoteOff = OFF
        NoteMiddleC = RED

    class DrumKit:
        First = RED
        Second = OFF
        Third = AMBER
        Fourth = GREEN

    class DefaultButton:
        On = ON
        Off = OFF


class SendToggleComponent(ControlSurfaceComponent):

    toggle_control = ButtonControl()

    def __init__(self, mixer, *args, **kwargs):
        super(SendToggleComponent, self).__init__(*args, **kwargs)
        self.mixer = mixer
        self.set_toggle_button = self.toggle_control.set_control_element

    @toggle_control.pressed
    def toggle_button_pressed(self, _button):
        if self.mixer.num_sends:
            self.mixer.send_index = \
                (self.mixer.send_index + 1) % self.mixer.num_sends


class InstrumentComponent(CompoundComponent):

    velocity_buttons = RadioButtonGroup()
    FEEDBACK_CHANNELS = ALL_FEEDBACK_CHANNELS

    @depends(show_message=None, log_message=None)
    def __init__(self, show_message=None, log_message=None, *a, **k):
        super(InstrumentComponent, self).__init__(*a, **k)
        self._show_message = show_message
        self._log_message = log_message
        self._velocity = 0
        self._channel = self.FEEDBACK_CHANNELS[0]
        self._grid_offset = 0
        self._grid_buttons = None
        self._channel_banking = self.register_component(ScrollComponent())
        self._channel_banking.can_scroll_up = self._can_channel_bank_up
        self._channel_banking.can_scroll_down = self._can_channel_bank_down
        self._channel_banking.scroll_up = self._channel_bank_up
        self._channel_banking.scroll_down = self._channel_bank_down
        self._grid_banking = self.register_component(ScrollComponent())
        self._grid_banking.can_scroll_up = self._can_grid_bank_up
        self._grid_banking.can_scroll_down = self._can_grid_bank_down
        self._grid_banking.scroll_up = self._grid_bank_up
        self._grid_banking.scroll_down = self._grid_bank_down
        self.set_velocity_buttons = self.velocity_buttons.set_control_element

    def _show(self, message):
        if self._show_message:
            self._show_message(message)

    def _log(self, message):
        if self._log_message:
            self._log_message(message)

    def set_grid_buttons(self, grid_buttons):
        self._grid_buttons = grid_buttons

        if self._grid_buttons:
            width = self._grid_buttons.width()
            height = self._grid_buttons.height()
            if width != 8 or height != 8:
                message = 'The grid is (%d, %d) and not (8, 8)' % (width, height)
                raise AssertionError, message

        self._remap_grid_buttons()

    def set_channel_bank_up_button(self, button):
        self._channel_banking.set_scroll_up_button(button)

    def set_channel_bank_down_button(self, button):
        self._channel_banking.set_scroll_down_button(button)

    def _can_channel_bank_up(self):
        return self._channel < self.FEEDBACK_CHANNELS[-1]

    def _can_channel_bank_down(self):
        return self.FEEDBACK_CHANNELS[0] < self._channel

    def _channel_bank_up(self):
        self._channel += 1
        self._remap_grid_buttons()

    def _channel_bank_down(self):
        self._channel -= 1
        self._remap_grid_buttons()

    def set_grid_bank_up_button(self, button):
        self._grid_banking.set_scroll_up_button(button)

    def set_grid_bank_down_button(self, button):
        self._grid_banking.set_scroll_down_button(button)

    def _grid_bank_delta(self):
        return 1

    def _can_grid_bank_up(self):
        return self._grid_offset + self._grid_bank_delta() + 63 < 128

    def _can_grid_bank_down(self):
        return 0 < self._grid_offset

    def _grid_bank_up(self):
        self._grid_offset += self._grid_bank_delta()
        self._remap_grid_buttons()

    def _grid_bank_down(self):
        self._grid_offset -= self._grid_bank_delta()
        self._remap_grid_buttons()

    @velocity_buttons.checked
    def _on_velocity_changed(self, button):
        self._velocity = button.index
        self._remap_grid_buttons()

    def _remap_grid_buttons(self):
        if self._grid_buttons:
            self._grid_buttons.reset()
            for y in xrange(8):
                for x in xrange(8):
                    (enabled, identifier, color) = self._map_note(x, y)
                    reverse_y = 7 - y
                    button = self._grid_buttons.get_button(x, reverse_y)
                    if enabled:
                        button.set_channel(self._channel)
                        button.set_identifier(identifier)
                    else:
                        button.set_channel(NON_FEEDBACK_CHANNEL)
                        button.set_identifier(0)
                    button.force_next_send()
                    button.set_light(color)

        actual_velocity = (self._velocity + 1) * 16 - 1
        # TODO(phs): how to tell Live to change the (fixed, default)
        # velocity on my non-haptic controller surface?

    def _map_note(self, x, y):
        raise AssertionError, 'Override in subclass'


class Scale(object):
    def __init__(self, notes):
        self._notes = notes
        self._length = len(self._notes)

    def length(self):
        return self._length

    def note(self, index):
        enabled, pitch_offset, color = self._notes[index % self.length()]
        pitch = (index / self.length()) * 12 + pitch_offset

        if enabled and pitch is 60:
            color = 'Piano.NoteMiddleC'

        if pitch >= 128:
            enabled = False
            pitch = 0
            color = 'Piano.NoteOff'

        return (enabled, pitch, color)

class PianoComponent(InstrumentComponent):

    layout_button = ButtonControl()
    FEEDBACK_CHANNELS = PIANO_FEEDBACK_CHANNELS
    FULL_SCALE = Scale([
        (True, 0, 'Piano.NoteBase'),
        (True, 1, 'Piano.NoteOff'),
        (True, 2, 'Piano.NoteLit'),
        (True, 3, 'Piano.NoteOff'),
        (True, 4, 'Piano.NoteLit'),
        (True, 5, 'Piano.NoteLit'),
        (True, 6, 'Piano.NoteOff'),
        (True, 7, 'Piano.NoteLit'),
        (True, 8, 'Piano.NoteOff'),
        (True, 9, 'Piano.NoteLit'),
        (True, 10, 'Piano.NoteOff'),
        (True, 11, 'Piano.NoteLit')])
    BRIEF_SCALE = Scale([
        (True, 0, 'Piano.NoteBase'),
        (True, 2, 'Piano.NoteOff'),
        (True, 4, 'Piano.NoteLit'),
        (True, 5, 'Piano.NoteOff'),
        (True, 7, 'Piano.NoteLit'),
        (True, 9, 'Piano.NoteOff'),
        (True, 11, 'Piano.NoteOff'),
        (True, 12, 'Piano.NoteBase')])

    def __init__(self, *a, **k):
        super(PianoComponent, self).__init__(*a, **k)
        self._full_layout = True
        self._grid_offset = 24
        self.set_layout_button = self.layout_button.set_control_element

    def _scale(self):
        if self._full_layout:
            return self.FULL_SCALE
        else:
            return self.BRIEF_SCALE

    @layout_button.pressed
    def _on_layout_changed(self, button):
        self._full_layout = not self._full_layout

        if self._full_layout:
            self._grid_offset = 24
        else:
            self._grid_offset = 8

        self._remap_grid_buttons()

    def _grid_bank_delta(self):
        return 8

    def _can_grid_bank_up(self):
        return self._map_note(0, 8)[1] != 0

    def _map_note(self, x, y):
        return self._scale().note(self._grid_offset + 8 * y + x)


class DrumKitComponent(InstrumentComponent):

    FEEDBACK_CHANNELS = DRUM_KIT_FEEDBACK_CHANNELS
    PAD_COLORS = [
        'DrumKit.First',
        'DrumKit.Second',
        'DrumKit.Third',
        'DrumKit.Fourth']

    def __init__(self, *a, **k):
        super(DrumKitComponent, self).__init__(*a, **k)
        self._grid_offset = self._grid_bank_delta()

    def _grid_bank_delta(self):
        return 4

    def _map_note(self, x, y):
        index = self._grid_offset + x + 4 * y
        if x >= 4:
            index += 28

        pad = (index + 12) / 16
        return (True, index, self.PAD_COLORS[pad % 4])


class APC_mini(OptimizedControlSurface):
    """ phs' hacked Akai APC mini Controller """

    def __init__(self, *a, **k):
        super(APC_mini, self).__init__(*a, **k)
        self._suggested_input_port = "Akai APC mini (phs)"
        self._suggested_output_port = "Akai APC mini (phs)"
        self._device_selection_follows_track_selection = True

        with self.component_guard():
            width = 8
            height = 8

            def button(identifier, *a, **k):
                return ButtonElement(
                    True,
                    MIDI_NOTE_TYPE,
                    NON_FEEDBACK_CHANNEL,
                    identifier,
                    skin=Skin(Colors),
                    *a, **k)

            def slider(identifier, *a, **k):
                return SliderElement(
                    MIDI_CC_TYPE,
                    NON_FEEDBACK_CHANNEL,
                    identifier,
                    *a, **k)

            shift_button = button(98, resource_type=SharedResource)
            def shift(button):
                return ComboElement(button, modifiers=[shift_button])

            master_volume = slider(56)
            sliders = ButtonMatrixElement(
                rows=[[slider(i + 48) for i in xrange(width)]])

            track_button_list = [button(64 + i) for i in xrange(width)]
            track_buttons = ButtonMatrixElement(rows=[track_button_list])

            up_button = shift(track_button_list[0])
            down_button = shift(track_button_list[1])
            left_button = shift(track_button_list[2])
            right_button = shift(track_button_list[3])
            volume_button = shift(track_button_list[4])
            pan_button = shift(track_button_list[5])
            send_button = shift(track_button_list[6])
            device_button = shift(track_button_list[7])

            scene_button_list = [button(i + 82) for i in xrange(height)]
            scene_buttons = ButtonMatrixElement(rows=[scene_button_list])

            stop_button = shift(scene_button_list[0])
            solo_button = shift(scene_button_list[1])
            arm_button = shift(scene_button_list[2])
            mute_button = shift(scene_button_list[3])
            select_button = shift(scene_button_list[4])
            piano_button = shift(scene_button_list[5])
            drum_kit_button = shift(scene_button_list[6])
            stop_all_button = shift(scene_button_list[7])

            grid_buttons = ButtonMatrixElement(rows=[[
                button(x + width * (height - y - 1))
                for x in xrange(width)]
                for y in xrange(height)])

            session = SpecialSessionComponent(
                num_tracks = width,
                num_scenes = height,
                auto_name=True,
                enable_skinning=True,
                is_enabled=False,
                layer=Layer(
                    scene_launch_buttons=scene_buttons,
                    clip_launch_buttons=grid_buttons,
                    stop_all_clips_button=stop_all_button))

            for scene_index in xrange(height):
                for track_index in xrange(width):
                    slot = session.scene(scene_index).clip_slot(track_index)
                    slot.layer = Layer(select_button=shift_button)

            self.set_highlighting_session_component(session)

            mixer = MixerComponent(
                width,
                auto_name=True,
                is_enabled=False,
                invert_mute_feedback=True)

            mixer.master_strip().layer = Layer(volume_control=master_volume)
            session.set_mixer(mixer)

            device = DeviceComponent(is_enabled=False)
            self.set_device_component(device)

            has_transport = False
            if has_transport:
                play_button = button(91)
                record_button = button(93)

                def play_toggle_model_transform(value):
                    return False if shift_button.is_pressed() else value

                transport = TransportComponent(
                    is_enabled=False,
                    play_toggle_model_transform=play_toggle_model_transform,
                    layer=Layer(
                        play_button=play_button,
                        record_button=record_button))

            piano = PianoComponent()
            drum_kit = DrumKitComponent()

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

            session_bank_mode = layer_mode(session,
                track_bank_left_button=left_button,
                track_bank_right_button=right_button,
                scene_bank_up_button=up_button,
                scene_bank_down_button=down_button)

            stop_track_mode = layer_mode(session, stop_track_clip_buttons=track_buttons)
            solo_mode = layer_mode(mixer, solo_buttons=track_buttons)
            arm_mode = layer_mode(mixer, arm_buttons=track_buttons)
            mute_mode = layer_mode(mixer, mute_buttons=track_buttons)
            select_mode = layer_mode(mixer, track_select_buttons=track_buttons)
            piano_mode = layer_mode(piano,
                grid_buttons=grid_buttons,
                velocity_buttons=track_buttons,
                layout_button=piano_button,
                channel_bank_up_button=right_button,
                channel_bank_down_button=left_button,
                grid_bank_up_button=up_button,
                grid_bank_down_button=down_button)
            drum_kit_mode = layer_mode(drum_kit,
                grid_buttons=grid_buttons,
                velocity_buttons=track_buttons,
                channel_bank_up_button=right_button,
                channel_bank_down_button=left_button,
                grid_bank_up_button=up_button,
                grid_bank_down_button=down_button)

            track_modes = ModesComponent(is_enabled=False)
            track_modes.add_mode('clip_stop', [stop_track_mode, session_bank_mode])
            track_modes.add_mode('solo', [solo_mode, session_bank_mode])
            track_modes.add_mode('arm', [arm_mode, session_bank_mode])
            track_modes.add_mode('mute', [mute_mode, session_bank_mode])
            track_modes.add_mode('select', [select_mode, session_bank_mode])
            track_modes.add_mode('piano', piano_mode)
            track_modes.add_mode('drum_kit', drum_kit_mode)
            track_modes.selected_mode = 'clip_stop'
            track_modes.layer = Layer(
                clip_stop_button=stop_button,
                solo_button=solo_button,
                arm_button=arm_button,
                mute_button=mute_button,
                select_button=select_button,
                piano_button=piano_button,
                drum_kit_button=drum_kit_button)

            self._disabled_during_handshake = [
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
