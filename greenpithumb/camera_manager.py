import logging
import os
import picamera

logger = logging.getLogger(__name__)

# Format of filename to write for camera image file (assumes timestamp is in
# UTC), as YYYY-MM-DDTHH:MMZ (minutes-level precision).
_FILENAME_FORMAT_FULL_RES = 'full_%Y-%m-%dT%H%MZ.jpg'
_FILENAME_FORMAT_REDUCED_RES = 'reduced_%Y-%m-%dT%H%MZ.jpg'
# Light level below which camera will not capture photos.
LIGHT_THRESHOLD_PCT = 20
# Camera rotation defined as [0,1,2,3 ~ 0,90,180,270 degrees]
CAMERA_ROTATION = 0   

class CameraManager(object):
    """Captures and saves photos to the filesystem."""

    def __init__(self, image_path, clock, light_sensor):
        """Creates a new camera manager instance.

        Args:
            image_path: Path name of the folder where images will be stored.
            clock: Clock interface.
            light_sensor: An interface for reading the light level.
        """
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        self._image_path = image_path        
        self._clock = clock
        self._camera = picamera.PiCamera(resolution=picamera.PiCamera.MAX_RESOLUTION)
        self._camera.rotation = CAMERA_ROTATION
        self._light_sensor = light_sensor

    def sufficient_light(self):
        """Checks if there is sufficient light to capture a photo.

        Returns:
            A boolean indicating whether or not there is sufficient light.
        """
        if self._light_sensor.light() >= LIGHT_THRESHOLD_PCT:
            return True
        return False

    def save_photo_full_res(self):
        """Captures a full resolution image from the camera and saves it to the filesystem."""
        
        # Set camera resolution
        #~ self._camera.resolution = (2592, 1944)
        
        # Capure photo
        path = os.path.join(self._image_path, self._clock.now().strftime(_FILENAME_FORMAT_FULL_RES))        
        self._camera.capture(path)
        
        logger.info('saved new reduced resolution photo to %s', path)  
        
        
    def save_photo_reduced_res(self):
        """Captures a reduced resolution image from the camera and saves it to the filesystem."""
        
        # Set camera resolution
        #~ self._camera.resolution = (640, 480)
        
        # Capure photo
        path = os.path.join(self._image_path, self._clock.now().strftime(_FILENAME_FORMAT_REDUCED_RES))        
        self._camera.capture(path, resize=(640, 480))   # Use resize() to capture reduced size images
        
        logger.info('saved new reduced resolution photo to %s', path)        
        

    def close(self):
        """Closes the camera.

        Should be called when use of the camera is complete.
        """
        self._camera.close()
