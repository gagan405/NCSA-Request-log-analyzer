import os
import glob
import re
import collections

from bisect import bisect_right
from datetime import datetime, timedelta
from collections import Counter
from itertools import groupby

LOG_DIR = '/var/log/oms/'


def get_log_file_to_search_for(date):
    access_log_files = glob.glob(LOG_DIR + 'access-*')
    dates = sorted([datetime.strptime(re.search('access-(.+?).log', x).group(1), "%Y_%m_%d") for x in access_log_files])
    i = bisect_right(dates, date)
    return LOG_DIR + "access-"+ dates[i-1].strftime("%Y_%m_%d") + ".log"


def get_hourly_stats(file_name, date):
    date_string = date.strftime("%d/%b/%Y")
    stats = {}
    with open(file_name, 'r') as f:
        for access in f:
            if date_string in access:
                idx = access.index(date_string) + len(date_string)+1
                hour = access[idx : idx+2]
                existing_stats = stats.get(hour, [])
                existing_stats.append(from_line(access, date_string, hour))
                stats[hour] = existing_stats
    for k,v in stats.iteritems():
        stats[k] = sorted(v, AccessRequest.latency_comparator, reverse=True)
    return stats

def from_line(line, date_string, hour):
    api = line.split('"')[1::2][0]
    return AccessRequest(date_string,
                        hour,
                        line.split('"')[1::2][0],
                        int(line.split(' ')[-4]),
                        int(line.split(' ')[-3]),
                        int(line.split(' ')[-1]))

def get_overall_stats(hourly_stats):
    f = Counter({})
    total_number_of_api_calls = 0
    hourly_api_counts = {}
    total_apis_crossing_hundred = 0
    total_apis_crossing_five_hundred = 0
    total_apis_crossing_one_second = 0
    apis_with_max_latencies = {}
    slowest_apis = set()

    for k,v in hourly_stats.iteritems():
        f += Counter(v)
        total_number_of_api_calls += len(v)
        hourly_api_counts[k] = len(v)
        hundreds = filter(lambda x: x.latency > 100, v)
        five_hundreds = filter(lambda x: x.latency > 500, v)
        one_seconds = filter(lambda x: x.latency > 1000, v)
        total_apis_crossing_hundred += len(hundreds)
        total_apis_crossing_five_hundred += len(five_hundreds)
        total_apis_crossing_one_second += len(one_seconds)

        slowest_apis.update(v[:20])

    return {"total_number_of_api_calls" : total_number_of_api_calls,
            "frequency_of_apis": f,
            "hourly_api_counts" : hourly_api_counts,
            "total_apis_crossing_hundred" : total_apis_crossing_hundred,
            "total_apis_crossing_five_hundred" : total_apis_crossing_five_hundred,
            "total_apis_crossing_one_second" : total_apis_crossing_one_second,
            "slowest_apis" : sorted(list(slowest_apis), reverse=True)[:20]
            }

class AccessRequest:

    def __init__(self, date_string, hour, api, return_status, bytes_returned, latency):
        self.date_string = date_string
        self.hour = hour
        self.api = api
        self.return_status = return_status
        self.bytes_returned = bytes_returned
        self.latency = latency

    def __str__(self):
        return '\t'.join([self.date_string, self.hour, self.api, str(self.return_status), str(self.bytes_returned), str(self.latency)])

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.api == other.api
        return False

    def __hash__(self):
        return hash(self.api)

    def __gt__(self, other):
        return self.latency > other.latency

    def __lt__(self, other):
        return self.latency < other.latency

    def __ge__(self, other):
        return self.latency >= other.latency

    def __le__(self, other):
        return self.latency <= other.latency

    def latency_comparator(request1, request2):
        return cmp(request1.latency, request2.latency)


if __name__ == '__main__':
    yesterday = datetime.today() - timedelta(days=1)
    log_file = get_log_file_to_search_for(yesterday)
    hourly_stats = get_hourly_stats(log_file, yesterday)
    stats = get_overall_stats(hourly_stats)

    print("Total number of APIs called on " + yesterday.strftime("%Y_%m_%d") + " : " + str(stats['total_number_of_api_calls']))
    print('')

    print("Most commonly used 20 APIs : \n")
    for item, count in stats['frequency_of_apis'].most_common(20):
        print(str(count) + ": " + item.api)

    print('')
    print("Hourly API counts : \n")

    for hour, count in sorted(stats['hourly_api_counts'].iteritems()):
        print(hour + ": " + str(count))

    print('')
    print("Total APIs crossing latency of 100 ms : " + str(stats['total_apis_crossing_hundred']))
    print('')
    print("Total APIs crossing latency of 500 ms : " + str(stats['total_apis_crossing_five_hundred']))
    print('')
    print("Total APIs crossing latency of 1s : " + str(stats['total_apis_crossing_one_second']))
    print('')
    print("APIs with max latencies : \n")
    for api in stats['slowest_apis']:
        print(api)

