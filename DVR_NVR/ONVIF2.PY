import socket
import requests
from onvif import ONVIFCamera
from onvif import ONVIFService

def scan_ip_network(local_ip_prefix):
    """
    Scan the network for IP devices using common ports for NVR/DVR systems.
    """
    found_devices = []
    for i in range(1, 10):
        ip = f"{local_ip_prefix}.{i}"
        print(f"Scanning {ip}...")
        try:
            # Check common NVR ports
            with socket.create_connection((ip, 80), timeout=1):
                found_devices.append(ip)
                print(f"Found device at {ip}")
        except (socket.timeout, ConnectionRefusedError):
            pass
    return found_devices

def discover_cameras_on_onvif(ip, port, user, password):
    """
    Discover cameras on the NVR using ONVIF protocol.
    """
    try:
        camera = ONVIFCamera(ip, port, user, password)
        media_service = camera.create_media_service()
        profiles = media_service.GetProfiles()
        
        for profile in profiles:
            print(f"Camera Found: {profile.Name}")
            
            # Prepare StreamSetup for the stream URI request
            stream_setup = {
                'Stream': 'RTP-Unicast',  # or 'RTP-Multicast' based on your requirements
                'Transport': {'Protocol': 'RTSP'}
            }
            
            # Get the stream URI for each profile
            stream_uri = media_service.GetStreamUri(StreamSetup=stream_setup, ProfileToken=profile.token)
            print(f"Camera Stream URL: {stream_uri.Uri}")
    
    except Exception as e:
        print(f"Error discovering cameras on {ip}: {e}")

def main():
    local_ip_prefix = '192.168.1'  # Adjust this to your network's IP prefix
    devices = scan_ip_network(local_ip_prefix)
    if devices:
        print(f"Devices found: {devices}")
        ip = devices[0]  # Choose first device for demonstration
        print(f"Discovering cameras on {ip} using ONVIF...")
        discover_cameras_on_onvif('192.168.1.14', 8080, 'root', 'root')  # Use actual login credentials
    else:
        print("No devices found.")

if __name__ == "__main__":
    main()
