"""
Simplified python script for getting the current state of a connected XInput device (such as an xbox controller).
Uses Windows' XInput library to access controllers.
http://msdn.microsoft.com/en-gb/library/windows/desktop/ee417001%28v=vs.85%29.aspx

- Dan Forbes - Mid October 2022
"""
import ctypes
import pyxboxcontroller.XInput as XInput

class XboxControllerState:
    """
    Parses an XInputState Struct into a sensible representation.\n
    Some examples of accessing the states' values:\n
    >>> left_thumbstick_x = state.l_thumb_x
    >>> right_thumbstick_y = state.r_thumb_y
    >>> x_pressed:bool = state.x
    >>> lb_pressed:bool = state.lb
    \n
    Alternately buttons can be gotten with:\n
    >>> button_pressed:bool = state.buttons["button"]
    """
    
    # Button map represents the bitmasks for each button encoded in gamepad.buttons. 
    # See https://learn.microsoft.com/en-us/windows/win32/api/xinput/ns-xinput-xinput_gamepad
    _BUTTON_MAP:dict[str, int] = {
    "dpad_up" : 1,
    "dpad_down" : 2,
    "dpad_left" : 4,
    "dpad_right" : 8,
    "start" : 16,
    "select": 32,
    "L3" : 64,
    "R3" : 128,
    "LB": 256,
    "RB" : 512,
    "a":4096,
    "b":8192,
    "x":16384,
    "y":32768,  
    }
       
    def __init__(self, state:XInput.XINPUT_STATE):
        gamepad:XInput.XINPUT_GAMEPAD = state.gamepad
        buttons:int = gamepad.buttons

        # # NOTE FOR DEBUG
        # if buttons not in self.BUTTON_MAP.values():
        #     print(f"Unknown button or combination: {buttons}")
        
        # Buttons
        self.buttons = {btn : self._get_button_state(btn, buttons) for btn in self._BUTTON_MAP}
        
        # Thumbsticks
        # TODO add deadzone checking
        # round to 4 decimal places, ignores the error with converting signed 32-bit int (-32768 to 32767) to float (-1.0 to 1.0)
        self.l_thumb_x:float = round(gamepad.l_thumb_x / 32767., 4)
        self.l_thumb_y:float = round(gamepad.l_thumb_y / 32767., 4)
        self.r_thumb_x:float = round(gamepad.r_thumb_x / 32767., 4)
        self.r_thumb_y:float = round(gamepad.r_thumb_y / 32767., 4)
        
        # Triggers
        self.l_trigger:float = round(gamepad.left_trigger / 255., 4)
        self.r_trigger:float = round(gamepad.right_trigger / 255., 4)
    
    def __repr__(self) -> str:
        return f"Buttons:{self.buttons}, Left thumbstick: {(self.l_thumb_x, self.l_thumb_y)}, Right thumbstick: {(self.r_thumb_x, self.r_thumb_y)}, Left trigger: {self.l_trigger}, Right trigger: {self.r_trigger}"

    def _get_button_state(self, button:str, buttons:int) -> bool:
        """Returns a boolean value for the given button based on the bitwise and of its bitmask and the buttons number"""
        mask:int = self._BUTTON_MAP[button]
        pressed:bool = (mask & buttons) != 0
        return pressed
    
    # Individual button helper functions
    @property
    def a(self) -> bool:
        return self.buttons["a"]
    @property
    def b(self) -> bool:
        return self.buttons["b"]
    @property
    def x(self) -> bool:
        return self.buttons["x"]
    @property
    def y(self) -> bool:
        return self.buttons["y"]
    @property
    def lb(self) -> bool:
        return self.buttons["lb"]
    @property
    def rb(self) -> bool:
        return self.buttons["rb"]
    @property
    def start(self) -> bool:
        return self.buttons["start"]
    @property
    def select(self) -> bool:
        return self.buttons["select"]
    @property
    def dpad_up(self) -> bool:
        return self.buttons["dpad_up"]
    @property
    def dpad_down(self) -> bool:
        return self.buttons["dpad_down"]
    @property
    def dpad_right(self) -> bool:
        return self.buttons["dpad_right"]
    @property
    def dpad_left(self) -> bool:
        return self.buttons["dpad_left"]
    @property
    def l3(self) -> bool:
        return self.buttons["l3"]
    @property
    def r3(self) -> bool:
        return self.buttons["r3"]


class XboxController:
    """
    Try id=0 when only one controller is connected. 
    >>> my_controller = XboxController(id)
    The state of the controller at the requested time is given by:
    >>> my_controller.state
    """
    
    # TODO
    # Deadzones
    # Rumble
    # Battery info
        
    def __init__(self, controller_id:int):
        self.id = controller_id
        self._state = XInput.XINPUT_STATE()
        self._last_packet_number:int = -1
        self._last_state:XboxControllerState = None
        
    @property
    def state(self) -> XboxControllerState:
        """Get the current state of the controller"""

        # Get controller state from XInput
        res = XInput.XINPUT_DLL.XInputGetState(self.id, ctypes.byref(self._state))
        
        # Handle response from XInput
        match res:
            
            case XInput.ErrorCodes.SUCCESS:
                packet_number = self._state.packet_number  # Get current packet number        
                if (packet_number == self._last_packet_number):  # No packets from controller since last call
                    return self._last_state
                else:  # Change in controller state
                    # Convert XInput struct into sensible response
                    new_state = XboxControllerState(self._state)  
                    
                    # Recall latest packet
                    self._last_packet_number = packet_number
                    self._last_state = new_state
                    
                    return new_state
                    
            case XInput.ErrorCodes.NOT_CONNECTED:
                raise RuntimeError(f"No controller connected with id: {self.id}")
            
            case _ as exc:
                raise RuntimeError(f"Unknown error {res} attempting to get state of device {self.id}") from exc      