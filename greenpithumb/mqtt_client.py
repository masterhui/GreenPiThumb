import logging
import threading
import paho.mqtt.client as mqtt


logger = logging.getLogger(__name__)

MQTT_TOPIC = "greenpi"


class MqttClient(object):
    """Wrapper for mqtt connection.

    Connects to mqtt broker.
    """

    def __init__(self, mqtt_broker):
        """Creates a new MqttClient object.

        Args:
            mqtt_broker: IP address of the mqtt broker.
        """
        self._mqtt_broker = mqtt_broker

        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self.on_connect
        self._mqtt_client.on_message = self.on_message
        self._mqtt_client.connect(self._mqtt_broker, 1883, 60)
        self._mqtt_client.loop_start()
        
        self._lock = threading.Lock()


    def on_connect(self, client, userdata, flags, rc):
        logger.info('Connected to mqtt borker %s', self._mqtt_broker)
        self._mqtt_client.subscribe(MQTT_TOPIC)
        logger.info('Subscribed to topic %s', MQTT_TOPIC)


    def on_message(self, client, userdata, msg):
        logger.info('Received mqtt message: %s', msg.payload)
        
