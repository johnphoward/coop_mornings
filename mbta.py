# Module to handle all gathering + delivery of info from MBTA API
import requests
import time

api_base_url = 'http://realtime.mbta.com/developer/api/v2/'
mbta_api_key = 'KNW697_Ya06mCt918f-Diw'

orange_line_stop_list = [
	'Oak Grove',
	'Malden',
	'Wellington',
	'Assembly',
	'Sullivan Square',
	'Community College',
	'North Station',
	'Haymarket',
	'State Street',
	'Downtown Crossing',
	'Chinatown',
	'Tufts Medical Center',
	'Back Bay',
	'Massachusetts Avenue',
	'Ruggles',
	'Roxbury Crossing',
	'Jackson Square',
	'Stony Brook',
	'Green Street',
	'Forest Hills Orange Line'
]

blue_line_stop_list = [
	'Wonderland',
	'Revere Beach',
	'Beachmont',
	'Suffolk Downs',
	'Orient Heights', 
	'Wood Island',
	'Airport', 
	'Maverick',
	'Aquarium',
	'State Street',
	'Government Center',
	'Bowdoin'
]

red_line_ashmont_stop_list = [
	'Alewife',
	'Davis', 
	'Porter', 
	'Harvard', 
	'Central', 
	'Kendall/MIT', 
	'Charles/MGH', 
	'Park Street',
	'Downtown Crossing',
	'South Station',
	'Broadway',
	'Andrew',
	'JFK/UMASS Ashmont',
	'Savin Hill',
	'Fields Corner',
	'Shawmut',
	'Ashmont'
]

red_line_braintree_stop_list = [
	'Alewife',
	'Davis', 
	'Porter', 
	'Harvard', 
	'Central', 
	'Kendall/MIT', 
	'Charles/MGH', 
	'Park Street',
	'Downtown Crossing',
	'South Station',
	'Broadway',
	'Andrew',
	'JFK/UMASS Braintree',
	'North Quincy',
	'Wollaston',
	'Quincy Center',
	'Quincy Adams',
	'Braintree',
]

mbta_stops = {
	'Orange': orange_line_stop_list,
	'Blue': blue_line_stop_list,
	'Red': red_line_ashmont_stop_list + red_line_braintree_stop_list,
	'Red - Ashmont': red_line_ashmont_stop_list,
	'Red - Braintree': red_line_braintree_stop_list
}


class Train():
	def __init__(self, json_data, line):
		self.line = line
		self.direction = json_data['trip_headsign']
		self.train_name = json_data['trip_name']

		self.upcoming_stops = []
		for stop in json_data['stop']:
			station = stop['stop_name']
			if '-' in station:
				split_name = station.split(' - ')
				station_name = split_name[0]
				direction = split_name[1]
			else:
				station_name = station
				direction = 'Terminus'
			stop_details = {
				'station': station_name,
				'arrival_time': float(stop['sch_arr_dt']),
				'direction': direction
			}
			self.upcoming_stops.append(stop_details)

		temp = self.train_name.split(' from ')
		self.start_time = temp[0]
		temp = temp[1].split(' to ')
		self.start_station = temp[0]
		self.end_station = temp[1]
		line_name = self.line
		if self.line == 'Red':
			if self.start_station == 'Alewife':
				station_name = self.end_station.split()[0]
			else:
				station_name = self.start_station.split()[0]
			line_name += ' - ' + station_name
		this_line = mbta_stops[line_name]
		self.line_stations = this_line if self.end_station == this_line[-1] else [t for t in reversed(this_line)]

	def __str__(self):
		return str(self.train_name)

	def current_destination(self):
		return self.end_station

	def current_location(self):
		next = self.next_stop_name()
		index = self.line_stations.index(next)
		if index > 0:
			return self.line_stations[index - 1]
		else:
			return None

	def has_started(self):
		current_time = time.localtime()
		saved_time = self.start_time.split()[0]
		hours = int(saved_time.split(':')[0])
		if 'pm' in self.start_time or 'am' in self.start_time and hours == 12:
			hours += 12
		minutes = int(saved_time.split(':')[1])
		start_minutes = 60 * hours + minutes
		current_hours = current_time.tm_hour
		current_minutes = current_time.tm_min
		if current_hours == 0:
			current_hours = 24
		current_minutes = 60 * current_hours + current_minutes
		return current_minutes >= start_minutes

	def next_stop_name(self):
		if len(self.upcoming_stops):
			return self.upcoming_stops[0]['station']
		else:
			return None

	def next_stop_time_arriving(self):
		if len(self.upcoming_stops):
			local_time = time.localtime(self.upcoming_stops[0]['arrival_time'])
			return time.strftime('%I:%M %p', local_time)
		else:
			return None

	def next_stop_time_to(self):
		if len(self.upcoming_stops):
			time_to = self.upcoming_stops[0]['arrival_time'] - time.time()
			minutes = int(time_to) / 60
			return minutes if minutes > -1 else None
		else:
			return 0

	def time_arriving_at_station(self, station_name):
		for station_object in self.upcoming_stops:
			if station_object['station'] == station_name:
				local_time = time.localtime(station_object['arrival_time'])
				return time.strftime('%I:%M %p', local_time)
		return None

	def time_until_station(self, station_name):
		for station_object in self.upcoming_stops:
			if station_object['station'] == station_name:
				time_to = station_object['arrival_time'] - time.time()
				return int(time_to) / 60
		return None


class SubwayLine():
	def __init__(self, query_results):
		self.line_name = query_results['route_id']
		self.stop_list = mbta_stops[self.line_name]
		self.end_a = self.stop_list[0]
		self.end_b = self.stop_list[-1]
		first_direction = query_results['direction'][0]['trip']
		first_direction_trains = [Train(train, self.line_name) for train in first_direction]
		if first_direction_trains[0].end_station == self.end_a:
			self.trains_toward_a = first_direction_trains
			self.trains_toward_b = [Train(train, self.line_name) for train in query_results['direction'][1]['trip']]
		else:
			self.trains_toward_b = first_direction_trains
			self.trains_toward_a = [Train(train, self.line_name) for train in query_results['direction'][1]['trip']]
		self.alerts = query_results['alert_headers']

	def __str__(self):
		return self.line_name

	def arrival_predictions_for_station(self, station_name):
		train_schedule = {
			'station': station_name
		}
		to_a = []
		for train in self.trains_toward_a:
			time_to = train.time_until_station(station_name)
			if time_to and time_to > -2:
				to_a.append(
					{
						'direction': train.direction,
						'time_until': train.time_until_station(station_name),
						'time_arriving': train.time_arriving_at_station(station_name),
						'current_location': train.current_location()
					}
				)
		to_b = []
		for train in self.trains_toward_b:
			time_to = train.time_until_station(station_name)
			if time_to and time_to > -2:
				to_b.append(
					{
						'direction': train.direction,
						'time_until': train.time_until_station(station_name),
						'time_arriving': train.time_arriving_at_station(station_name),
						'current_location': train.current_location()
					}
				)
		train_schedule[self.end_a] = to_a
		train_schedule[self.end_b] = to_b
		return train_schedule

	def current_train_locations(self):
		to_a = [train.current_location() for train in self.trains_toward_a if train.current_location()]
		to_b = [train.current_location() for train in self.trains_toward_b if train.current_location()]
		train_locations = {
			self.end_a: to_a,
			self.end_b: to_b
		}
		return train_locations
		
def get_subway_line(line_color):
	"""
	Queries the MBTA api_v2 and returns a SubwayLine for the given color
	"""
	generic_params = {
		'api_key': mbta_api_key,
		'format': 'json',
		'route': line_color
	}
	query_type = 'predictionsbyroute'
	query_url = api_base_url + query_type + '?'
	for key, val in generic_params.items():
		query_url += key + '=' + val + '&'
	query_url = query_url[:-1]
	response = requests.get(query_url)
	data = response.json()
	subway_line = SubwayLine(data)
	return subway_line

line = get_subway_line('Orange')

def printArrivalTimesAtStation(line, station):
	arrivals = line.arrival_predictions_for_station(station)
	for direction in arrivals.keys():
		if direction != 'station':
			arrival_list = arrivals[direction]
			for arrival in arrival_list:
				print 'To: %s \t\t at %s (%d mins) - train currently at %s' % (arrival['direction'], arrival['time_arriving'], arrival['time_until'], arrival['current_location'])

printArrivalTimesAtStation(line, 'Ruggles')