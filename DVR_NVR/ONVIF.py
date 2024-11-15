from onvif import ONVIFCamera

def discover_cameras(ip, port, user, password):
    camera = ONVIFCamera(ip, port, user, password)
    media_service = camera.create_media_service()
    profiles = media_service.GetProfiles()

    for profile in profiles:
        print(f"Camera Found: {profile.Name}")
        
        # Retrieve stream URI for the profile
        stream_uri_request = media_service.create_type('GetStreamUri')
        stream_uri_request.ProfileToken = profile.token
        stream_uri_request.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
        stream_uri = media_service.GetStreamUri(stream_uri_request)
        
        print(f"Camera Stream URL: {stream_uri.Uri}")

# Example usage
discover_cameras('192.168.1.14', 8080, 'root', 'root')
