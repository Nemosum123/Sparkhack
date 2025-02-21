import RPi.GPIO as GPIO
import time
import os
import threading

from mfrc522 import SimpleMFRC522
from picamera2 import Picamera2
import qrcode
from PIL import Image
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas

# -------------------------------
# Configuration and Initialization
# -------------------------------

# Authorized RFID tag ID
AUTHORIZED_ID = 1047839255856

# OLED display dimensions and log file settings (for QR code)
OLED_WIDTH = 128
OLED_HEIGHT = 64
FILE_PATH = "/home/soham/examplelog.txt"   # log file to encode into QR code
SAVE_PATH = "/home/soham/qr_debug.png"       # temporary QR code image save path

# Directory for captured images
IMAGE_DIRECTORY = "/home/soham/captured_images"
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

# Initialize RFID reader (using SimpleMFRC522)
reader = SimpleMFRC522()

# Initialize OLED display (using I2C)
serial_oled = i2c(port=1, address=0x3C)
device = sh1106(serial_oled, width=OLED_WIDTH, height=OLED_HEIGHT)

# Initialize PiCamera2 for image capture
picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (1024, 768)})
picam2.configure(config)

# -------------------------------
# Global State Variables & Lock
# -------------------------------
current_card = None           # currently detected card ID (if any)
last_removed_time = None      # timestamp when a card was last removed
last_removed_authorized = False  # flag indicating if the removed card was authorized
image_captured = False        # flag to ensure image capture happens only once per removal event
qr_displayed = False          # flag to ensure QR display happens only once per removal event

state_lock = threading.Lock()  # to protect shared variables

# -------------------------------
# OLED Display & QR Code Functions
# -------------------------------
def display_message(message):
    """Display a text message on the OLED for 2 seconds and then clear it."""
    print(f"Displaying on OLED: {message}")
    with canvas(device) as draw:
        draw.text((30, 20), message, fill="white")
    time.sleep(2)
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")

def generate_qr_code(data):
    """Generate a QR code image from data."""
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white").convert("1")
    img.save(SAVE_PATH)
    print(f"✅ QR saved to {SAVE_PATH} (Dimensions: {img.size})")
    return img

def display_qr_native(image):
    """Display the QR code image on the OLED at its native resolution."""
    qr_width, qr_height = image.size
    x = (OLED_WIDTH - qr_width) // 2
    y = (OLED_HEIGHT - qr_height) // 2
    inverted_image = Image.eval(image, lambda x: 255 - x)
    with canvas(device) as draw:
        draw.bitmap((x, y), inverted_image, fill="white")
    print(f"Displaying QR at native resolution (position: {x}, {y})")
    time.sleep(5)
    device.clear()

def display_qr():
    """Read log data, generate a QR code, and display it on the OLED."""
    try:
        with open(FILE_PATH, "r") as f:
            data = f.read().strip()
            print(f"Data length: {len(data)} characters")
        qr_img = generate_qr_code(data)
        display_qr_native(qr_img)
    except Exception as e:
        print(f"Error in QR display: {e}")
        device.clear()

# -------------------------------
# Camera Capture Functionality
# -------------------------------
def capture_image():
    """Capture an image using the PiCamera2 when a timeout occurs."""
    global last_removed_time, image_captured, qr_displayed
    print("⏳ Timeout! Capturing image...")
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{IMAGE_DIRECTORY}/image_{timestamp}.jpg"
    picam2.start()
    time.sleep(2)  # Allow sensor to adjust
    picam2.capture_file(filename)
    picam2.stop()
    print(f"📸 Image saved as {filename}")
    time.sleep(10)  # Wait before resuming normal operations
    with state_lock:
        last_removed_time = None
        image_captured = False
        qr_displayed = False

# -------------------------------
# Thread Functions
# -------------------------------
def rfid_reader_thread():
    """Continuously read RFID cards and update display based on authorization."""
    global current_card, last_removed_time, last_removed_authorized, image_captured, qr_displayed
    while True:
        id, text = reader.read_no_block()  # non-blocking read
        with state_lock:
            if id is not None:
                # Card detected – if different from the last one, update state and show message
                if current_card != id:
                    current_card = id
                    if id == AUTHORIZED_ID:
                        display_message("AUTHORIZED")
                    else:
                        display_message("UNAUTHORIZED")
                    # Reset removal-related state
                    last_removed_time = None
                    image_captured = False
                    qr_displayed = False
            else:
                # No card detected: if a card was previously present, record its removal time
                if current_card is not None:
                    last_removed_time = time.time()
                    last_removed_authorized = (current_card == AUTHORIZED_ID)
                    current_card = None
        time.sleep(0.1)

def timeout_handler_thread():
    """Handle timeout actions: capture image after 5 seconds and, for an authorized removal, display QR after 6 seconds."""
    global last_removed_time, image_captured, qr_displayed
    while True:
        with state_lock:
            if last_removed_time is not None:
                elapsed = time.time() - last_removed_time
                # Trigger camera capture after 5 seconds if not already done
                if elapsed >= 5 and not image_captured:
                    image_captured = True
                    threading.Thread(target=capture_image, daemon=True).start()
                # If the removed card was authorized, trigger QR display after 6 seconds
                if last_removed_authorized and elapsed >= 6 and not qr_displayed:
                    qr_displayed = True
                    threading.Thread(target=display_qr, daemon=True).start()
        time.sleep(0.1)

# -------------------------------
# Main Entry Point
# -------------------------------
def main():
    try:
        # Start both the RFID reader and timeout handler threads
        reader_thread = threading.Thread(target=rfid_reader_thread, daemon=True)
        timeout_thread = threading.Thread(target=timeout_handler_thread, daemon=True)
        reader_thread.start()
        timeout_thread.start()
        # Keep the main thread alive indefinitely
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Program stopped by user.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()import RPi.GPIO as GPIO
import time
import os
import threading

from mfrc522 import SimpleMFRC522
from picamera2 import Picamera2
import qrcode
from PIL import Image
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas

# -------------------------------
# Configuration and Initialization
# -------------------------------

# Authorized RFID tag ID
AUTHORIZED_ID = 1047839255856

# OLED display dimensions and log file settings (for QR code)
OLED_WIDTH = 128
OLED_HEIGHT = 64
FILE_PATH = "/home/soham/examplelog.txt"   # log file to encode into QR code
SAVE_PATH = "/home/soham/qr_debug.png"       # temporary QR code image save path

# Directory for captured images
IMAGE_DIRECTORY = "/home/soham/captured_images"
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

# Initialize RFID reader (using SimpleMFRC522)
reader = SimpleMFRC522()

# Initialize OLED display (using I2C)
serial_oled = i2c(port=1, address=0x3C)
device = sh1106(serial_oled, width=OLED_WIDTH, height=OLED_HEIGHT)

# Initialize PiCamera2 for image capture
picam2 = Picamera2()
config = picam2.create_still_configuration(main={"size": (1024, 768)})
picam2.configure(config)

# -------------------------------
# Global State Variables & Lock
# -------------------------------
current_card = None           # currently detected card ID (if any)
last_removed_time = None      # timestamp when a card was last removed
last_removed_authorized = False  # flag indicating if the removed card was authorized
image_captured = False        # flag to ensure image capture happens only once per removal event
qr_displayed = False          # flag to ensure QR display happens only once per removal event

state_lock = threading.Lock()  # to protect shared variables

# -------------------------------
# OLED Display & QR Code Functions
# -------------------------------
def display_message(message):
    """Display a text message on the OLED for 2 seconds and then clear it."""
    print(f"Displaying on OLED: {message}")
    with canvas(device) as draw:
        draw.text((30, 20), message, fill="white")
    time.sleep(2)
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")

def generate_qr_code(data):
    """Generate a QR code image from data."""
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white").convert("1")
    img.save(SAVE_PATH)
    print(f"✅ QR saved to {SAVE_PATH} (Dimensions: {img.size})")
    return img

def display_qr_native(image):
    """Display the QR code image on the OLED at its native resolution."""
    qr_width, qr_height = image.size
    x = (OLED_WIDTH - qr_width) // 2
    y = (OLED_HEIGHT - qr_height) // 2
    inverted_image = Image.eval(image, lambda x: 255 - x)
    with canvas(device) as draw:
        draw.bitmap((x, y), inverted_image, fill="white")
    print(f"Displaying QR at native resolution (position: {x}, {y})")
    time.sleep(5)
    device.clear()

def display_qr():
    """Read log data, generate a QR code, and display it on the OLED."""
    try:
        with open(FILE_PATH, "r") as f:
            data = f.read().strip()
            print(f"Data length: {len(data)} characters")
        qr_img = generate_qr_code(data)
        display_qr_native(qr_img)
    except Exception as e:
        print(f"Error in QR display: {e}")
        device.clear()

# -------------------------------
# Camera Capture Functionality
# -------------------------------
def capture_image():
    """Capture an image using the PiCamera2 when a timeout occurs."""
    global last_removed_time, image_captured, qr_displayed
    print("⏳ Timeout! Capturing image...")
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{IMAGE_DIRECTORY}/image_{timestamp}.jpg"
    picam2.start()
    time.sleep(2)  # Allow sensor to adjust
    picam2.capture_file(filename)
    picam2.stop()
    print(f"📸 Image saved as {filename}")
    time.sleep(10)  # Wait before resuming normal operations
    with state_lock:
        last_removed_time = None
        image_captured = False
        qr_displayed = False

# -------------------------------
# Thread Functions
# -------------------------------
def rfid_reader_thread():
    """Continuously read RFID cards and update display based on authorization."""
    global current_card, last_removed_time, last_removed_authorized, image_captured, qr_displayed
    while True:
        id, text = reader.read_no_block()  # non-blocking read
        with state_lock:
            if id is not None:
                # Card detected – if different from the last one, update state and show message
                if current_card != id:
                    current_card = id
                    if id == AUTHORIZED_ID:
                        display_message("AUTHORIZED")
                    else:
                        display_message("UNAUTHORIZED")
                    # Reset removal-related state
                    last_removed_time = None
                    image_captured = False
                    qr_displayed = False
            else:
                # No card detected: if a card was previously present, record its removal time
                if current_card is not None:
                    last_removed_time = time.time()
                    last_removed_authorized = (current_card == AUTHORIZED_ID)
                    current_card = None
        time.sleep(0.1)

def timeout_handler_thread():
    """Handle timeout actions: capture image after 5 seconds and, for an authorized removal, display QR after 6 seconds."""
    global last_removed_time, image_captured, qr_displayed
    while True:
        with state_lock:
            if last_removed_time is not None:
                elapsed = time.time() - last_removed_time
                # Trigger camera capture after 5 seconds if not already done
                if elapsed >= 5 and not image_captured:
                    image_captured = True
                    threading.Thread(target=capture_image, daemon=True).start()
                # If the removed card was authorized, trigger QR display after 6 seconds
                if last_removed_authorized and elapsed >= 6 and not qr_displayed:
                    qr_displayed = True
                    threading.Thread(target=display_qr, daemon=True).start()
        time.sleep(0.1)

# -------------------------------
# Main Entry Point
# -------------------------------
def main():
    try:
        # Start both the RFID reader and timeout handler threads
        reader_thread = threading.Thread(target=rfid_reader_thread, daemon=True)
        timeout_thread = threading.Thread(target=timeout_handler_thread, daemon=True)
        reader_thread.start()
        timeout_thread.start()
        # Keep the main thread alive indefinitely
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Program stopped by user.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
