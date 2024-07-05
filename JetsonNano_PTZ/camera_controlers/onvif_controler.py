import time

from onvif import ONVIFCamera

# Initialize the ONVIFCamera instance

from onvif import ONVIFCamera
from time import sleep


class PTZCamera:
    def __init__(self, ip, port, user, password):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.camera = ONVIFCamera(self.ip, self.port, self.user, self.password)
        self.media_service = self.camera.create_media_service()
        #self.ptz_service = self.camera.create_ptz_service()
        self.profile = self.media_service.GetProfiles()[0]
        self.token = self.profile.token
        #self.requestc = self.ptz_service.create_type('ContinuousMove')
        #self.requestc.ProfileToken = self.token
        #self.stop_request = self.ptz_service.create_type('Stop')
        #self.stop_request.ProfileToken = self.token

        #self._initialize_zoom()

    def _initialize_zoom(self):
        config_options = self._get_ptz_configuration_options()
        if self.requestc.Velocity is None:
            status = self.ptz_service.GetStatus({'ProfileToken': self.token})
            self.requestc.Velocity = status.Position
            self.requestc.Velocity.Zoom.space = config_options.Spaces.ContinuousZoomVelocitySpace[0].URI

    def _get_ptz_configuration_options(self):
        request = self.ptz_service.create_type('GetConfigurationOptions')
        request.ConfigurationToken = self.profile.PTZConfiguration.token
        return self.ptz_service.GetConfigurationOptions(request)

    def zoom(self, velocity):
        self.requestc.Velocity.Zoom.x = velocity
        self.ptz_service.ContinuousMove(self.requestc)

    def stop(self):
        self.stop_request.PanTilt = False
        self.stop_request.Zoom = True
        self.ptz_service.Stop(self.stop_request)


if __name__ == "__main__":
    camera_ip = '192.168.20.249'
    camera_port = 8000
    camera_user = 'admin'
    camera_password = 'admin'

    camera = PTZCamera(ip=camera_ip, port=camera_port, user=camera_user, password=camera_password)
    print(camera)
