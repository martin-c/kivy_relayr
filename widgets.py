# coding=utf-8
import json
from kivy import Logger
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
import datetime
from kivy.properties import NumericProperty, DictProperty
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.animation import Animation
from kivy.garden.graph import Graph, MeshLinePlot
import settings


class MainWidget(BoxLayout):
    def __init__(self, devices, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.devices = {}
        for device in devices:
            widget = DeviceWidget()
            widget.device_id = device.id
            self.devices[device.id] = widget
            self.add_widget(widget)

    def update(self, topic, payload):
        Logger.info("main: update for %s" % topic)
        payload = json.loads(payload)
        device_id = payload['deviceId']
        readings = payload['readings']
        self.devices[device_id].update(readings)


class SensorHistoryWidget(Graph):
    values = ListProperty()
    timestamps = ListProperty()
    meaning = StringProperty('temperature')

    def configure(self):
        self.ylabel = settings.UNITS[self.meaning]
        self.ymin = settings.VALUE_BORDERS[self.meaning][0]
        self.ymax = settings.VALUE_BORDERS[self.meaning][1]
        self.plot.color = settings.MEANING_COLORS[self.meaning]

    def __init__(self, *args, **kwargs):
        super(SensorHistoryWidget, self).__init__(*args, **kwargs)
        self.plot = MeshLinePlot()
        self.add_plot(self.plot)
        self.configure()

    def add_value(self, value, timestamp):
        self.values.append(value)
        self.timestamps.append(timestamp)

        new_points = []
        for i in xrange(len(self.timestamps)):
            v = self.values[i]
            t = self.timestamps[i]
            read_time = datetime.datetime.fromtimestamp(t / 1e3)
            read_ago = datetime.datetime.now() - read_time
            new_points.append((int(-read_ago.total_seconds()), v))
        self.plot.points = new_points

        self.xmin = self.plot.points[0][0]
        self.xmax = self.plot.points[-1][0] + 1


class DeviceWidget(BoxLayout):
    device_id = StringProperty("ddd")

    name_label = ObjectProperty()
    sensor_container = ObjectProperty()

    def __init__(self, **kwargs):

        super(DeviceWidget, self).__init__(**kwargs)
        self.sensors = {}
        self.history = SensorHistoryWidget()
        self.add_widget(self.history)

    def on_device_id(self, device, device_id):
        self.name_label.text = device_id

    def update(self, readings):
        for reading in readings:
            meaning = reading['meaning']
            if meaning not in self.sensors:
                sensor = SensorWidget()
                sensor.meaning = meaning
                self.sensors[meaning] = sensor
                self.sensor_container.add_widget(sensor)
            self.sensors[meaning].timestamp = reading['recorded']
            self.sensors[meaning].value = reading['value']

            if meaning == self.history.meaning:
                self.history.add_value(reading['value'], reading['recorded'])


class SensorWidget(BoxLayout):
    meaning = StringProperty()
    value = NumericProperty()
    timestamp = NumericProperty()

    center_label = ObjectProperty()

    color = ObjectProperty([0, 0, 0, 1])

    angle = NumericProperty()

    LABEL_PATTERN = "%s\n[b][size=20sp]%s %s[/size][/b]\n[color=918a6fff]%s sec ago[/color]"

    def update(self, sensor, value):
        read_time = datetime.datetime.fromtimestamp(self.timestamp / 1e3)

        read_ago = datetime.datetime.now() - read_time

        unit = settings.UNITS.get(self.meaning, "")
        self.center_label.text = self.LABEL_PATTERN % (self.meaning, self.value, unit, int(read_ago.total_seconds()))
        self.color = settings.MEANING_COLORS.get(self.meaning, (.5, 5, .5, 1))

        min_value, max_value = settings.VALUE_BORDERS.get(self.meaning, (None, None))
        if min_value is None:
            self.angle = 360
        else:
            interval = max_value - min_value
            percentage = (float(self.value) - min_value) / interval
            Animation(angle=360 * percentage, d=.5, t='in_out_cubic').start(self)

    on_meaning = on_value = on_timestamp = update
