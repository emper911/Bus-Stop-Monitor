import requests as req
from datetime import datetime
import time
from serial import Serial, SerialException

# KEY_MTA_SUBWAY = "36609299ae8a8626734517878b1a15df"

class ArduinoBusStopViewer:

    def __init__(self, mta_bus_api_key, bus_stop_code_1, bus_stop_code_2, bluetooth_path):
        """
        This Object gets stop information from the mta bus REST API and parses the information
        into a readable format to send to an Arduino over bluetooth, displaying
        buses less than 5 stops away through LED lights and times of the nearest bus from both directions.
        """
        self.bus_stop_direction_1 = 1
        self.bus_stop_direction_2 = 2
        self.mta_bus_api = MTABusStopAPI (
            mta_bus_api_key, 
            bus_stop_code_1, 
            bus_stop_code_2
        )
        self.ser = Serial(bluetooth_path, 9600)
        

    def start(self):

        while True:
            #gets mta data for stop 1 and 2
            print("To Utica A and C Train")
            buses_in_progress_1, next_bus_1 = self.mta_bus_api.get_bus_info(
                                                                        self.bus_stop_direction_1
                                                                    )
            print("To Utica 3 and 4 Train")
            buses_in_progress_2, next_bus_2 = self.mta_bus_api.get_bus_info(
                                                                        self.bus_stop_direction_2
                                                                    )
            next_bus_1 = self._next_bus_formatter(next_bus_1)
            next_bus_2 = self._next_bus_formatter(next_bus_2)

            self.attempt_serial_write(
                buses_in_progress_1, buses_in_progress_2,
                next_bus_1, next_bus_2
            )

            time.sleep(28)

    def attempt_serial_write(self, buses_in_progress_1, buses_in_progress_2, next_bus_1, next_bus_2):
         
        attempts = 0
        while attempts < 3:
            try:
                time.sleep(1)
                self._serial_write(
                    buses_in_progress_1, buses_in_progress_2,
                    next_bus_1, next_bus_2
                )
                break
            except SerialException:
                print("Disconnected! Attempting to reconnect:")
                attempts += 1
                print("\tAttempts to re-connect: {}".format(attempts))
                self.ser.close()
                time.sleep(2)
                self.ser.open()
                time.sleep(2)

        if attempts < 3:
            print("Message Sent!")
        else:
            print("Unable to connect")


    def _serial_write(self, buses_in_progress_1, buses_in_progress_2, next_bus_1, next_bus_2):
        """
        Writes inputs to arduino over bluetooth
        """
        #formats inputs into arduino readable string
        send_serial_string = self._format_serial_string(
            buses_in_progress_1, 
            buses_in_progress_2,
            next_bus_1,
            next_bus_2,
        )
        print(send_serial_string)
        # Converts serial string to byte form and writes to serial to bluetooth
        send_serial_byte = send_serial_string.encode('utf-8')
        self.ser.write(send_serial_byte)


    def _format_serial_string(self, buses_in_progress_1, buses_in_progress_2, next_bus_1, next_bus_2):
        """
        Formats serial string to send to arduino
        return: '<05550000000000>' 
                < 
                    05 -- bus_stop 1 mins away,
                    55 -- bus_stop 2 mins away, 
                    00000 bus 1 LEDs,
                    00000 bus 2 LEDs 
                > 
        """
        
        led_array = self._led_light_formatter(
            buses_in_progress_1, 
            buses_in_progress_2
        )
        #-- start marker
        send_serial_string = "<" 
        #appending time in mins of next bus at stop 1 and stop 2
        send_serial_string += "{0:02}{1:02}".format(
            next_bus_1,
            next_bus_2
        )
        #appending led array
        send_serial_string += ''.join(map(str, led_array))
        #-- end marker
        send_serial_string += ">"
        return send_serial_string

        
    def _next_bus_formatter(self, next_bus):
        """
        Checks input of next_bus and provides appropriate format
        """
        if next_bus > 60 or next_bus == None:
            return - 1 
        else:
            return next_bus


    def _led_light_formatter(self, buses_in_progress_1, buses_in_progress_2):
        """
        Formats what bus stop lights to turn on or keep off
        """
        led_light_array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if buses_in_progress_1 != None:
            for i in range(len(buses_in_progress_1)):
                #if buses are less than 5 stops away
                if buses_in_progress_1[i][1] < 5:
                    #1 to turn on led at the bus stop
                    led_light_array[buses_in_progress_1[i][1]] = 1

        if buses_in_progress_2 != None:
            for i in range(len(buses_in_progress_2)):
                #if buses are less than 5 stops away
                if buses_in_progress_2[i][1] < 5:
                    #1 to turn on led at the bus stop
                    led_light_array[buses_in_progress_2[i][1] + 5] = 1

        return led_light_array


class MTABusStopAPI:

    def __init__(self, mta_key, bus_stop_1, bus_stop_2):
        """
        """
        self.mta_api_url_1 = self._bus_stop_url_formatter(mta_key, bus_stop_1)
        self.mta_api_url_2 = self._bus_stop_url_formatter(mta_key, bus_stop_2)


    def _bus_stop_url_formatter(self, key, bus_stop, direction=None, minimal=True):
        """
        Formats url to call MTA Bus API
        """
        if direction != None:
            if minimal:
                return "http://bustime.mta.info/api/siri/stop-monitoring.json?key={0}&version=2&DirectionRef={1}&OperatorRef=MTA&MonitoringRef={2}&StopMonitoringDetailLevel=basic".format(key, direction, bus_stop)
            else:
                return "http://bustime.mta.info/api/siri/stop-monitoring.json?key={0}&version=2&DirectionRef={1}&OperatorRef=MTA&MonitoringRef={2}".format(key, direction, bus_stop)
        else:
            if minimal:
                return "http://bustime.mta.info/api/siri/stop-monitoring.json?key={0}&version=2&OperatorRef=MTA&MonitoringRef={1}&StopMonitoringDetailLevel=basic".format(key, bus_stop)
            else:
                return "http://bustime.mta.info/api/siri/stop-monitoring.json?key={0}&version=2&OperatorRef=MTA&MonitoringRef={1}".format(key, bus_stop)


    def get_bus_info(self, stop=1):
        if stop == 1:
            return self._get_buses_enroute(self.mta_api_url_1)
        elif stop == 2:
            return self._get_buses_enroute(self.mta_api_url_2)


    def _get_buses_enroute(self, url):
        """
        Sends request to mta api and parses the response into desired format.
        """
        try:
            res_json = req.get(url).json()
        except:
            print("Could not Connect to MTA API")
            return (None, None)

        buses_enroute = res_json['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']

        if len(buses_enroute) > 0:
            #near_buses: (stops away, mins_away), #next_bus 'in minutes': minutes away
            near_buses, next_bus = self._get_nearest_buses(buses_enroute)
            return (near_buses, next_bus)
        else:
            return (None, None)


    def _get_nearest_buses(self, buses_enroute, distance_in_stops=10):
        """
        Loops through a list of buses in transit. If bus is less than 10 stops away then returns list of tuples
        with stops away and mins away. As well as the minutes away of the closest bus.
        If no bus is less than 10 stops away then still returns the minutes away of the nearest bus.

        RETURN: (
            near_buses (list): [(bus_id, stops_away, mins_away), ... ], 
            next_bus (int): time in minutes -- type int
        )
        """
        near_buses = []
        next_bus_mins = -1

        for i in range(len(buses_enroute)):

            near_buses, next_bus_mins = self._single_bus_format_(
                buses_enroute[i],
                near_buses,
                next_bus_mins,
                distance_in_stops
            )

        print("\n")
        if len(near_buses) > 0:
            return (near_buses, next_bus_mins)
        else:
            return (None, next_bus_mins)


    def _single_bus_format_(self, bus_enroute, near_buses, next_bus_mins, distance_in_stops):
        """
        """
        #should have expected arrival time, skips over if not available
        if 'ExpectedArrivalTime' not in bus_enroute['MonitoredVehicleJourney']['MonitoredCall'].keys():
            return near_buses, next_bus_mins

        bus_id = bus_enroute['MonitoredVehicleJourney']['VehicleRef']
        stops_away = bus_enroute['MonitoredVehicleJourney']['MonitoredCall']['NumberOfStopsAway']
        expected_arrival_time = bus_enroute['MonitoredVehicleJourney']['MonitoredCall']['ExpectedArrivalTime']
        mins_away = self._format_time(expected_arrival_time)

        #next_bus_mins is the closest bus to the stop in minutes
        if next_bus_mins > mins_away or next_bus_mins == -1:
            next_bus_mins = mins_away

        #Checks if stops are less than threshold provided
        if stops_away < distance_in_stops:
            #FORMAT for near_buses
            near_buses.append((bus_id, stops_away, mins_away))
            print("A bus is {0} stops away. Minutes Away: {1}".format(
                stops_away, mins_away))

        return near_buses, next_bus_mins


    def _format_time(self, expected_arrival_time):
        #Formats time string to datetime object
        formatted_expected_arrival_time = datetime.strptime(
            expected_arrival_time[:-10], "%Y-%m-%dT%H:%M:%S")
        #Subtracts the current time from expected arrival time.
        time_away = formatted_expected_arrival_time - datetime.now()
        mins_away = time_away.seconds//60
        return mins_away


if __name__ == "__main__":
    RASPBERRY_PI_HC_06_PATH = '/dev/rfcomm2'
    MTA_BUS_API_KEY = "4d30d5c7-070e-4e6d-8e3a-b8a513976940"
    #CLOSEST STOPS FROM HOME
    UTICA_TO_WILLIAMSBURG_BUS_STOP_CODE = "307093"
    UTICA_TO_KINGS_PLAZA_BUS_STOP_CODE = "303676"

    arduino_bus_stop_viewer = ArduinoBusStopViewer(
        MTA_BUS_API_KEY,
        UTICA_TO_WILLIAMSBURG_BUS_STOP_CODE,
        UTICA_TO_KINGS_PLAZA_BUS_STOP_CODE,
        RASPBERRY_PI_HC_06_PATH
    )
    arduino_bus_stop_viewer.start()

