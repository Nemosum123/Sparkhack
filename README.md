# Sparkhack
Smart Medicine Inventory Management System

📌 Project Overview

This project involves a smart medicine inventory management system using a Raspberry Pi Zero 2 W, RFID authentication, a camera module, and an OLED display to track medicine usage and automate log transfer. The system consists of four medicine compartments, each monitored by an RFID-RC522 module to detect when a drawer is opened and closed. Additionally, RFID authentication is implemented, where specific RFID tags are pre-classified as authorized or unauthorized users.

When an RFID tag (attached beneath the drawer) comes into contact with the reader and then moves away, the Raspberry Pi is triggered after a delay (to stabilize lighting) to capture an image using the REE552 night vision camera module. The captured image is processed using OpenCV edge detection and object recognition to count remaining medicine strips. The log, containing timestamps and medicine consumption data, is updated in a local file.

For data transfer, a QR code containing the log is dynamically generated and displayed on a 1.3” OLED screen (only when a manual switch is turned on). The QR can be scanned using a smartphone to store logs locally. The system operates in passive mode, ensuring the Pi is only activated when triggered by an RFID event, optimizing power consumption.

🚀 Features

✅ Automated Medicine Tracking: Uses RFID to detect when a medicine drawer is opened.
✅ RFID-Based Authentication: The system supports authorized and unauthorized RFID tags, displaying messages on the OLED screen when a user taps their card.
✅ Image-Based Medicine Counting: The REE552 Night Vision Camera captures medicine strips and processes the count using OpenCV.
✅ QR Code-Based Log Transfer: The OLED screen displays a QR code, allowing offline log transfer.
✅ Passive Power Mode: The Raspberry Pi is only activated when RFID detects movement, conserving power.
✅ Error Prevention: A few-second delay before image capture ensures proper lighting conditions.
✅ Data Logging & Forecasting: The system stores all usage logs for predicting medicine needs over time.
✅ User-Friendly Interface: Scannable QR codes eliminate the need for internet-dependent data transfer.

📌 RFID Authentication System

The RFID system now supports user authentication:

Authorized RFID Tags: When an authorized RFID tag is tapped, the OLED screen displays 'AUTHORIZED', allowing medicine access.

Unauthorized RFID Tags: When an unauthorized RFID tag is tapped, the OLED screen displays 'UNAUTHORIZED', denying access.

Dynamic User Verification: The system supports multiple pre-registered RFID tags, allowing flexible authentication.


📦 Hardware Components

📌 System Overview

The project consists of a smart container divided into four compartments, each monitored by an RFID-RC522 module. When a drawer is opened:

1. RFID detects movement and powers on the Raspberry Pi.


2. The RFID system checks if the user is authorized or unauthorized.


3. The camera captures an image of the medicine strips inside.


4. OpenCV processes the image, counting how many strips remain.


5. The system updates the log with the current medicine count.


6. A QR code is generated and displayed on the OLED screen.


7. The user scans the QR code to retrieve the medicine log.



📌 Software & Libraries

📌 QR Code-Based Data Transfer

The system eliminates NFC dependency and instead uses QR code-based data transfer:

1. Log Format (Stored Locally & Encoded in QR Code)



{
  "date": "2025-02-20",
  "log": [
    {"time": "08:00 AM", "medicine": "Paracetamol 500mg", "quantity": 1},
    {"time": "12:00 PM", "medicine": "Vitamin C 1000mg", "quantity": 1},
    {"time": "06:00 PM", "medicine": "Ibuprofen 200mg", "quantity": 2},
    {"time": "09:00 PM", "medicine": "Aspirin 75mg", "quantity": 1}
  ]
}

2. QR Code is Generated on the Pi



import qrcode
log_data = "Medicine Log: 08:00 AM - Paracetamol, 12:00 PM - Vitamin C"
qr = qrcode.make(log_data)
qr.save("/home/pi/medicine_log.png")

3. User Scans the QR Code



The QR does not require an internet connection.

The user can store and access logs offline.


🚀 Future Improvements

🔹 AI-Based Pill Recognition → Using YOLO or MobileNet for detecting individual pills.
🔹 OCR for Expiry Date & Batch Number → Extract text from medicine labels.
🔹 Automated Medicine Refill Alerts → Predict when new stock is needed.
🔹 Cloud Syncing (Optional) → If needed, allow users to upload logs to a cloud database.

📌 Conclusion

This smart medicine tracking system automates inventory management using RFID-based sensing, image recognition, and QR-based logging. It ensures efficient medicine tracking while incorporating user authentication via RFID for controlled access. The system operates offline, making it ideal for hospitals, elderly care, and personal medicine tracking.

Would you like any modifications or additional details? 🚀
