import argparse
import contextlib
import datetime
import logging
import Queue
import time

import Adafruit_DHT
import Adafruit_MCP3008
#~ import picamera
import RPi.GPIO as GPIO

import adc_thread_safe
import camera_manager
import clock
import db_store
import dht22
import humidity_sensor
import light_sensor
import pi_io
import poller
import pump
import pump_history
import record_processor
import sleep_windows
#import soil_moisture_sensor
import vegetronix_vh400
import drain_sensor
import water_level_sensor
import temperature_sensor
import wiring_config_parser
import mqtt_client

logger = logging.getLogger(__name__)


def configure_logging(verbose):
    """Configure the root logger for log output."""
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-15s %(levelname)-4s %(message)s',
        '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    if verbose:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.WARNING)


def read_wiring_config(config_filename):
    """Parses wiring config from a file."""
    logger.info('reading wiring config at "%s"', config_filename)
    with open(config_filename) as config_file:
        return wiring_config_parser.parse(config_file.read())


def make_adc(wiring_config):
    """Creates ADC instance based on the given wiring_config.

    Args:
        wiring_config: Wiring configuration for the GreenPiThumb.

    Returns:
        An ADC instance for the specified wiring config.
    """
    # The MCP3008 spec and Adafruit library use different naming for the
    # Raspberry Pi GPIO pins, so we translate as follows:
    # * CLK -> CLK
    # * CS/SHDN -> CS
    # * DOUT -> MISO
    # * DIN -> MOSI
    return adc_thread_safe.Adc(
        Adafruit_MCP3008.MCP3008(
            clk=wiring_config.gpio_pins.mcp3008_clk,
            cs=wiring_config.gpio_pins.mcp3008_cs_shdn,
            miso=wiring_config.gpio_pins.mcp3008_dout,
            mosi=wiring_config.gpio_pins.mcp3008_din))


def make_dht22_sensors(wiring_config):
    """Creates sensors derived from the DHT22 sensor.

    Args:
        wiring_config: Wiring configuration for the GreenPiThumb.

    Returns:
        A two-tuple where the first element is a temperature sensor and the
        second element is a humidity sensor.
    """
    local_dht22 = dht22.CachingDHT22(
        lambda: Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, wiring_config.gpio_pins.dht22),
        clock.Clock())
    return temperature_sensor.TemperatureSensor(
        local_dht22), humidity_sensor.HumiditySensor(local_dht22),

def make_water_level_sensor(raspberry_pi_io, wiring_config):
    return water_level_sensor.WaterLevelSensor(
        raspberry_pi_io, wiring_config.gpio_pins.sonar)

def make_soil_moisture_sensor(adc, raspberry_pi_io, wiring_config):
    return vegetronix_vh400.SoilMoistureSensor(
        adc, raspberry_pi_io, wiring_config.adc_channels.soil_moisture_sensor,
        wiring_config.gpio_pins.soil_moisture_power)
        
def make_drain_sensor(adc, raspberry_pi_io, wiring_config):
    return drain_sensor.DrainSensor(
        adc, raspberry_pi_io, wiring_config.adc_channels.drain_sensor,
        wiring_config.gpio_pins.drain_sensor_power)        

def make_light_sensor(adc, wiring_config):
    return light_sensor.LightSensor(adc,
                                    wiring_config.adc_channels.light_sensor)
                                    
def make_mqtt_client(mqtt_broker):
    return mqtt_client.MqttClient(mqtt_broker)

def make_camera_manager(rotation, image_path, light_sensor):
    """Creates a camera manager instance.

    Args:
        rotation: The amount (in whole degrees) to rotate the camera image.
        image_path: The directory in which to save images.
        light_sensor: A light sensor instance.

    Returns:
        A CameraManager instance with the given settings.
    """
    #~ camera = picamera.PiCamera(resolution=picamera.PiCamera.MAX_RESOLUTION)
    #~ camera.rotation = 0 
    return camera_manager.CameraManager(image_path, clock.Clock(), light_sensor)


def make_pump_manager(moisture_threshold, sleep_windows, raspberry_pi_io,
                      wiring_config, pump_amount, db_connection, pump_interval, water_level_sensor):
    """Creates a pump manager instance.

    Args:
        moisture_threshold: The minimum moisture level below which the pump
            turns on.
        sleep_windows: Sleep windows during which pump will not turn on.
        raspberry_pi_io: pi_io instance for the GreenPiThumb.
        wiring_config: Wiring configuration for the GreenPiThumb.
        pump_amount: Amount (in mL) to pump on each run of the pump.
        db_connection: Database connection to use to retrieve pump history.
        pump_interval: Maximum amount of hours between pump runs.
        water_level_sensor: Interface to the water level sensor.

    Returns:
        A PumpManager instance with the given settings.
    """
    water_pump = pump.Pump(raspberry_pi_io, clock.Clock(), wiring_config.gpio_pins.pump)
    pump_scheduler = pump.PumpScheduler(clock.LocalClock(), sleep_windows)
    pump_timer = clock.Timer(clock.Clock(), pump_interval)
    last_pump_time = pump_history.last_pump_time(db_store.WateringEventStore(db_connection))
    if last_pump_time:
        logger.info('last watering was at %s', last_pump_time)
        time_remaining = max(datetime.timedelta(seconds=0), (last_pump_time + pump_interval) - clock.Clock().now())
    else:
        logger.info('no previous watering found')
        #~ time_remaining = datetime.timedelta(seconds=0)   # !!!WARNING!!! Immediately water plants if no previous watering event was found !!!WARNING!!!
        time_remaining = pump_interval                      # Schedule the first mandatory plant watering event in pump_interval hours
    logger.info('time until until next watering: %s', time_remaining)
    pump_timer.set_remaining(time_remaining)
    return pump.PumpManager(water_pump, pump_scheduler, moisture_threshold, pump_amount, pump_timer, water_level_sensor)


def make_sensor_pollers(poll_interval, photo_interval, record_queue, mqtt_client,
                        temperature_sensor, humidity_sensor, water_level_sensor,
                        soil_moisture_sensor, drain_sensor, light_sensor, camera_manager,
                        pump_manager):
    """Creates a poller for each GreenPiThumb sensor.

    Args:
        poll_interval: The frequency at which to poll non-camera sensors.
        photo_interval: The frequency at which to capture photos.
        record_queue: Queue on which to put sensor reading records.
        mqtt_client: The mqtt client for sending updates to openhab
        temperature_sensor: Sensor for measuring temperature.
        humidity_sensor: Sensor for measuring humidity.
        water_level_sensor: Sensor for measuring the reservoir water level.
        soil_moisture_sensor: Sensor for measuring soil moisture.
        drain_sensor: Sensor for measuring wheather water has drained through the plant pot.
        light_sensor: Sensor for measuring light levels.
        camera_manager: Interface for capturing photos.
        pump_manager: Interface for turning water pump on and off.

    Returns:
        A list of sensor pollers.
    """
    logger.info('creating sensor pollers (poll interval=%ds")',
                poll_interval.total_seconds())
    utc_clock = clock.Clock()

    make_scheduler_func = lambda: poller.Scheduler(utc_clock, poll_interval)
    photo_make_scheduler_func = lambda: poller.Scheduler(utc_clock, photo_interval)
    poller_factory = poller.SensorPollerFactory(make_scheduler_func, record_queue, mqtt_client)
    camera_poller_factory = poller.SensorPollerFactory(
        photo_make_scheduler_func, record_queue, mqtt_client)

    return [
        poller_factory.create_temperature_poller(temperature_sensor),
        poller_factory.create_humidity_poller(humidity_sensor),
        poller_factory.create_water_level_poller(water_level_sensor),
        poller_factory.create_soil_watering_poller(
            soil_moisture_sensor, drain_sensor, pump_manager),
        poller_factory.create_light_poller(light_sensor),
        camera_poller_factory.create_camera_poller(camera_manager)
    ]  # yapf: disable


def create_record_processor(db_connection, record_queue):
    """Creates a record processor for storing records in a database.

    Args:
        db_connection: Database connection to use to store records.
        record_queue: Record queue from which to process records.
    """
    return record_processor.RecordProcessor(
        record_queue,
        db_store.SoilMoistureStore(db_connection),
        db_store.LightStore(db_connection),
        db_store.HumidityStore(db_connection),
        db_store.TemperatureStore(db_connection),
        db_store.WaterLevelStore(db_connection),
        db_store.WateringEventStore(db_connection))


def main(args):
    configure_logging(args.verbose)
    logger.info('starting greenpithumb')
    wiring_config = read_wiring_config(args.config_file)
    record_queue = Queue.Queue()
    raspberry_pi_io = pi_io.IO(GPIO)
    adc = make_adc(wiring_config)
    local_soil_moisture_sensor = make_soil_moisture_sensor(
        adc, raspberry_pi_io, wiring_config)
    local_drain_sensor = make_drain_sensor(
        adc, raspberry_pi_io, wiring_config)
    local_temperature_sensor, local_humidity_sensor = make_dht22_sensors(
        wiring_config)
    local_water_level_sensor = make_water_level_sensor(
        raspberry_pi_io, wiring_config)        
    local_light_sensor = make_light_sensor(adc, wiring_config)
    camera_manager = make_camera_manager(args.camera_rotation, args.image_path,
                                         local_light_sensor)
    mqtt_client = make_mqtt_client(args.mqtt_broker)

    with contextlib.closing(
            db_store.open_or_create_db(args.db_file)) as db_connection:
        record_processor = create_record_processor(db_connection, record_queue)
        pump_manager = make_pump_manager(
            args.moisture_threshold,
            sleep_windows.parse(args.sleep_window),
            raspberry_pi_io,
            wiring_config,
            args.pump_amount,
            db_connection,
            datetime.timedelta(hours=args.pump_interval),
            local_water_level_sensor)
        pollers = make_sensor_pollers(
            datetime.timedelta(minutes=args.poll_interval),
            datetime.timedelta(minutes=args.photo_interval),
            record_queue,
            mqtt_client,
            local_temperature_sensor,
            local_humidity_sensor,
            local_water_level_sensor,
            local_soil_moisture_sensor,
            local_drain_sensor,
            local_light_sensor,
            camera_manager,
            pump_manager)
        try:
            for current_poller in pollers:
                current_poller.start_polling_async()
            while True:
                if not record_processor.try_process_next_record():
                    time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info('Caught keyboard interrupt. Exiting.')
        finally:
            for current_poller in pollers:
                current_poller.close()
            raspberry_pi_io.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='GreenPiThumb',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-a',
        '--pump_amount',
        type=int,
        help='Volume of water (in mL) to pump each time the water pump is run',
        default=200)
    parser.add_argument(
        '-p',
        '--poll_interval',
        type=float,
        help='Number of minutes between each sensor poll',
        default=15)
    parser.add_argument(
        '-t',
        '--photo_interval',
        type=float,
        help='Number of minutes between each camera photo',
        default=(4 * 60))
    parser.add_argument(
        '-w',
        '--pump_interval',
        type=float,
        help='Max number of hours between plant waterings',
        default=(365 * 24))
    parser.add_argument(
        '-c',
        '--config_file',
        help='Wiring config file',
        default='greenpithumb/wiring_config.ini')
    parser.add_argument(
        '-s',
        '--sleep_window',
        action='append',
        type=str,
        default=[],
        help=('Time window during which GreenPiThumb will not activate its '
              'pump. Window should be in the form of a time range in 24-hour '
              'format, such as "03:15-03:45 (in the local time zone)"'))
    parser.add_argument(
        '-i',
        '--image_path',
        type=str,
        help='Path to folder where images will be stored',
        default='images/')
    parser.add_argument(
        '-d',
        '--db_file',
        help='Location to store GreenPiThumb database file',
        default='greenpithumb/greenpithumb.db')
    parser.add_argument(
        '-m',
        '--moisture_threshold',
        type=int,
        help=('Moisture threshold to start pump. The pump will turn on if the '
              'moisture level drops below this level'),
        default=0)
    parser.add_argument(
        '--camera_rotation',
        type=int,
        choices=(0, 90, 180, 270),
        help='Specifies the amount to rotate the camera\'s image.')
    parser.add_argument(
        '--mqtt_broker',
        type=str,
        default=[],
        help='Specifies IP address of the mqtt broker.')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Use verbose logging')
    main(parser.parse_args())
