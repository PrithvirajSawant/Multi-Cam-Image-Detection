import cv2
import socket
import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

def list_usb_cameras():
    available_cameras = []
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Using CAP_DSHOW for Windows
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def scan_wifi_network_for_cameras():
    print("Scanning for cameras on the local WiFi network...")
    local_ip_prefix = socket.gethostbyname(socket.gethostname()).rsplit('.', 1)[0]
    common_ports = [554, 80]  # RTSP and HTTP
    found_devices = []
    lock = Lock()

    def scan_ip(ip):
        for port in common_ports:
            try:
                with socket.create_connection((ip, port), timeout=1):
                    with lock:
                        found_devices.append(f"{ip}:{port}")
                    print(f"Camera found at {ip}:{port}")
                    break
            except (socket.timeout, ConnectionRefusedError):
                pass

    with ThreadPoolExecutor(max_workers=10) as executor:
        ips = [f"{local_ip_prefix}.{i}" for i in range(1, 255)]
        executor.map(scan_ip, ips)

    return found_devices

def connect_to_camera(source):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Failed to connect to camera at source: {source}")
        return None
    print(f"Connected to camera at source: {source}")
    return cap

def start_stream(cap):
    print("Press 'q' to quit the stream.")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            break

        cv2.imshow("Camera Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def main():
    print("Welcome to the Camera Stream Program")
    print("Available Camera Types:")
    print("1. USB/Built-in Camera")
    print("2. IP Camera (RTSP or HTTP)")
    print("3. WiFi Network Camera Scan")

    choice = input("Select camera type (1, 2, or 3): ")

    if choice == '1':
        print("Scanning for USB/Built-in cameras...")
        usb_cameras = list_usb_cameras()
        if not usb_cameras:
            print("No USB cameras detected.")
            return
        print("Available USB cameras:", usb_cameras)
        camera_index = int(input("Enter camera index to connect: "))
        cap = connect_to_camera(camera_index)

    elif choice == '2':
        print("IP Camera selected.")
        ip_url = input("Enter the IP camera URL (RTSP or HTTP): ")
        cap = connect_to_camera(ip_url)

    elif choice == '3':
        print("Scanning WiFi network for cameras...")
        devices = scan_wifi_network_for_cameras()
        if not devices:
            print("No cameras found on the network.")
            return
        print("Found devices:", devices)
        
        device_index = input(f"Select device by index (0 to {len(devices)-1}), or enter custom RTSP/HTTP URL: ")
        if device_index.isdigit():
            ip_url = f"rtsp://{devices[int(device_index)]}/stream"
        else:
            ip_url = device_index  # assume it's a custom URL
        
        cap = connect_to_camera(ip_url)

    else:
        print("Invalid choice. Please select 1, 2, or 3.")
        return

    if cap:
        start_stream(cap)
    else:
        print("Could not start streaming due to connection issues.")

if __name__ == "__main__":
    main()
