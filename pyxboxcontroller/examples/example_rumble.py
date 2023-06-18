from pyxboxcontroller import XboxController, XboxBatteryInfo

if __name__ == "__main__":
    # Connect to controller
    controller = XboxController(0)
    
    # Send a rumble command
    controller.rumble((1.0, 1.0), 0.5)