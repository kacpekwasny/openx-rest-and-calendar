from dataclasses import dataclass, field
from sys import argv
from glob import glob
from argparse import ArgumentParser
from datetime import datetime, timedelta

from matplotlib.style import available


@dataclass
class Duration:
    start: datetime 
    end: datetime

def main():
    glob(f"{12}/*.txt")

def load_calendars(file_names: list[str]) -> dict[str, list[Duration]]:
    d: dict[str, list[Duration]] = {}
    for name in file_names:
        d[name] = []
        with open(name, "r", encoding="utf-8") as f:
            for line in f.read().split("\n"):
                striped = line.strip()
                if striped == "":
                    continue

                # the whole day is full
                if len(striped) == 10:
                    start = datetime.strptime(striped, '%Y-%m-%d')
                    d[name].append(Duration(start, start + timedelta(hours=23, minutes=59)))
                    continue

                # the duration of being busy is determined by two datetimes
                begin = striped[:19]
                end = striped[22:]
                time_format = '%Y-%m-%d %H:%M:%S'
                d[name].append(Duration(
                    start=datetime.strptime(begin, time_format),
                    end=datetime.strptime(end, time_format)
                ))

    return d


def find_available(calendars: dict[str, list[Duration]], duration: timedelta, n: int) -> datetime:
    """
    Find first available slot for this timedelta between all
    search if there are

    params:
        calendars:  dict[str, list[Duration]] - the calendars representing when the users are busy
        duration:   timedelta - how long does the free time slot have to be
        n:          how many users at the same time have to be free

    returns:
        None - if such datetime does not exist
        datetime - if a datetime that fullfils requirements was found
    """

    # edge cases:
    if len(calendars) > n:
        return None

    # 


def first_available_time(busy: list[Duration], duration: timedelta, search_from: datetime) -> datetime:
    second = timedelta(seconds=1)
    if len(busy) == 0 or busy[0].start - search_from >= duration:
        return search_from
    
    end_busy = busy[0].end
    for d in busy[1:]:
        if d.start - end_busy >= duration:
            return end_busy + second
        last = d
        end_busy = d.end

    return last.end + second

    




if __name__ == "__main__":
    parser = ArgumentParser(description="Find first available slot for at least specified number of people.")
    parser.add_argument("--duration-in-minutes", type=int, required=True)
    parser.add_argument("--minimum-people", type=int, required=True)
    parser.add_argument("--calendars", type=str, required=True)
    namespace = parser.parse_args(argv[1:])

    cal = namespace.calendars
    cal = cal[:-1] if cal[-1] == "/" else cal
    calendars = glob(f"{cal}/*.txt")

    calendars = load_calendars(calendars)
    for k, v in calendars.items():
        print(k, first_available_time(v, timedelta(minutes=30), datetime(2022, 7, 1)))
        for d in v:
            print(f"\t{d}")







def convert_calendars(calendars: dict[str, list[Duration]]) -> dict[str, list[Duration]]:
    """
    Convert
    """


