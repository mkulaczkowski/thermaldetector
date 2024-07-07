import logging
import time

from onvif import ONVIFCamera, ONVIFError

# Initialize the ONVIFCamera instance

from onvif import ONVIFCamera
from time import sleep


class PTZCamera:
    def __init__(self, ip, port, username, password):
        self.mycam = ONVIFCamera(ip, port, username, password)
        self.media_service = self.mycam.create_media_service()

        self.imaging_service = self.mycam.create_imaging_service()

        self.media_profile = self.media_service.GetProfiles()[0]
        # Get and print camera name and IP address
        device_info = self.mycam.devicemgmt.GetDeviceInformation()
        camera_name = device_info.Model
        camera_ip = ip

        print(f'Camera Name: {camera_name}')
        print(f'Camera IP Address: {camera_ip}')

        try:
            self.ptz_service = self.mycam.create_ptz_service()
        except ONVIFError as e:
            self.ptz_service = None
            logging.warning(f'Camera: {camera_name}, does not support PTZ')

    def get_stream_url(self):
        stream_setup = self.media_service.create_type('GetStreamUri')
        stream_setup.ProfileToken = self.media_profile.token
        stream_setup.StreamSetup = {
            'Stream': 'RTP-Unicast',
            'Transport': {'Protocol': 'RTSP'}
        }
        response = self.media_service.GetStreamUri(stream_setup)
        logging.info(f'URL: {response.Uri}')
        return response.Uri

    # Define the function to get stream resolution
    def get_stream_resolution(self):
        video_source_config = self.media_service.GetVideoSourceConfigurations()
        video_source_token = video_source_config[0].token
        video_source = self.media_service.GetVideoSources()
        for source in video_source:
            if source.token == video_source_token:
                resolution = source.Resolution
                return (resolution.Width, resolution.Height)

    def _get_ptz_configuration_options(self):
        request = self.ptz_service.create_type('GetConfigurationOptions')
        request.ConfigurationToken = self.profile.PTZConfiguration.token
        return self.ptz_service.GetConfigurationOptions(request)

    def set_contrast(self, contrast_value):
        imaging_settings = self.imaging_service.create_type('SetImagingSettings')
        imaging_settings.VideoSourceToken = self.media_profile.VideoSourceConfiguration.SourceToken
        imaging_settings.ImagingSettings = {
            'Contrast': contrast_value
        }
        imaging_settings.ForcePersistence = True
        self.imaging_service.SetImagingSettings(imaging_settings)

    def zoom(self, zoom_value):
        move = self.ptz_service.create_type('ContinuousMove')
        move.ProfileToken = self.media_profile.token
        move.Velocity = {
            'Zoom': {
                'x': zoom_value
            }
        }
        self.ptz_service.ContinuousMove(move)

    def stop_zoom(self):
        stop = self.ptz_service.create_type('Stop')
        stop.ProfileToken = self.media_profile.token
        stop.Zoom = True
        self.ptz_service.Stop(stop)


if __name__ == "__main__":
    camera_ip = '192.168.20.94'
    camera_port = 8899
    camera_user = 'admin'
    camera_password = 'admin'

    camera = PTZCamera(ip=camera_ip, port=camera_port, username=camera_user, password=camera_password)
    print(camera)
    # Get stream URL
    stream_url = camera.get_stream_url()
    print(f'Stream URL: {stream_url}')

    # Set contrast to 50
    camera.set_contrast(50)

    # Zoom in
    camera.zoom(0.1)
    # Wait a bit and then stop zoom
    import time

    time.sleep(2)
    camera.stop_zoom()