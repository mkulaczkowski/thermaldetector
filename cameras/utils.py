import os
import time

from onvif import ONVIFError

from JetsonNano_PTZ.camera_controlers.onvif_controler import PTZCamera
import logging

logger = logging.getLogger(__name__)


def connect_camera(ip, port, username, password, ptz_functions=True, retries=5, timeout=10):
    attempt = 0
    while attempt < retries:
        try:
            logger.info(f'Started Camera {ip}')
            return PTZCamera(ip=ip, port=port, username=username, password=password, ptz_functions=ptz_functions)
        except ONVIFError as e:
            attempt += 1
            if attempt < retries:
                logger.warning(f'Attempt {attempt} failed to connect to camera at {ip}:{port}, retrying...')
                time.sleep(timeout)
            else:
                logger.error(f'Cannot connect to camera at {ip}:{port} after {retries} attempts')
                return None


def connect_thermal_camera():
    thermal_camera_ptz = connect_camera(
        ip=os.getenv('THERMAL_CAMERA_IP', '192.168.137.102'),
        port=os.getenv('THERMAL_CAMERA_PORT', 8000),
        username=os.getenv('THERMAL_CAMERA_USER', 'admin'),
        password=os.getenv('THERMAL_CAMERA_PASS', 'admin'),
        ptz_functions=False
    )
    return thermal_camera_ptz


def connect_visible_camera():
    visible_camera_ptz = connect_camera(
        ip=os.getenv('VISIBLE_CAMERA_IP', '192.168.137.103'),
        port=os.getenv('VISIBLE_CAMERA_PORT', 8899),
        username=os.getenv('VISIBLE_CAMERA_USER', 'admin'),
        password=os.getenv('VISIBLE_CAMERA_PASS', 'admin')
    )
    return visible_camera_ptz
