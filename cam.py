from typing import Optional, Union
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
import cv2
import io

import cv2
import socket
from pydantic import BaseModel
import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

app = FastAPI()

# @app.get("/detect_cam")
def list_usb_cameras():
    available_cameras = []
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # First try with CAP_DSHOW
        if not cap.isOpened():
            cap = cv2.VideoCapture(i, cv2.CAP_MSMF)  # Try MSMF if DSHOW fails
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

# @app.get("/Scan_for_cam")
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

# @app.get("/connect_to_cam")
def connect_to_camera(source):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Failed to connect to camera at source: {source}")
        return None
    print(f"Connected to camera at source: {source}")
    return cap

# @app.get("/capture_image")
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

# @app.get("/select_cam")
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
    
# ///////////////////////////////////

@app.get("/test")
async def test_exception():
    raise HTTPException(status_code=403, detail="Unauthorized access")

# Endpoint to get all available cameras
@app.get("/get_available_cameras", summary="Get all available cameras")
def get_available_cameras():
    usb_cameras = list_usb_cameras()
    wifi_cameras = scan_wifi_network_for_cameras()

    available_cameras = {
        "usb_cameras_idx": usb_cameras,
        "wifi_cameras": wifi_cameras
    }

    if not usb_cameras and not wifi_cameras:
        raise HTTPException(status_code=404, detail="No cameras found.")

    return available_cameras

# Model to accept query parameters
class CameraRequest(BaseModel):
    camera_type: int
    ip_url: Optional[str] = None
    device_index: Optional[int] = None

@app.post("/select_cams", summary="Select a Camera Type", description="Select a camera type to start the stream. Available types:\n\n1. USB/Built-in Camera\n2. IP Camera (RTSP or HTTP)\n3. WiFi Network Camera Scan")
def select_cam(camera_request: CameraRequest):
    
    #  2nd method (Alt : desc)
    """
    **Welcome to the Camera Stream Program**

    **Available Camera Types:**
    - **1**: USB/Built-in Camera
    - **2**: IP Camera (RTSP or HTTP)
    - **3**: WiFi Network Camera Scan

    Select the appropriate camera type and provide any required details.
    """
    # choice = camera_request.camera_type
    # Code for handling the camera selection process

    
    print("Welcome to the Camera Stream Program")
    print("Available Camera Types:")
    print("1. USB/Built-in Camera")
    print("2. IP Camera (RTSP or HTTP)")
    print("3. WiFi Network Camera Scan")
    
    choice = camera_request.camera_type
    cap = None

    if choice == 1:
        print("Scanning for USB/Built-in cameras...")
        usb_cameras = list_usb_cameras()
        if not usb_cameras:
            raise HTTPException(status_code=404, detail="No USB cameras detected.")
        print("Available USB cameras:", usb_cameras)
        if camera_request.device_index is not None:
            cap = connect_to_camera(camera_request.device_index)
        else:
            raise HTTPException(status_code=400, detail="Camera index is required for USB camera.")

    elif choice == 2:
        print("IP Camera selected.")
        if camera_request.ip_url:
            cap = connect_to_camera(camera_request.ip_url)
        else:
            raise HTTPException(status_code=400, detail="IP camera URL is required.")

    elif choice == 3:
        print("Scanning WiFi network for cameras...")
        devices = scan_wifi_network_for_cameras()
        if not devices:
            raise HTTPException(status_code=404, detail="No cameras found on the network.")
        print("Found devices:", devices)
        
        if camera_request.device_index is not None:
            ip_url = f"rtsp://{devices[camera_request.device_index]}/stream"
            cap = connect_to_camera(ip_url)
        elif camera_request.ip_url:
            cap = connect_to_camera(camera_request.ip_url)  # custom URL input
        else:
            raise HTTPException(status_code=400, detail="Device index or custom URL is required for WiFi camera.")

    else:
        raise HTTPException(status_code=400, detail="Invalid camera type selected.")

    if cap:
        start_stream(cap)
        return {"message": "Camera stream started successfully."}
    else:
        raise HTTPException(status_code=500, detail="Could not start streaming due to connection issues.")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    