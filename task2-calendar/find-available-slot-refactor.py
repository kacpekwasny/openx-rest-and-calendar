

from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, timedelta
from glob import glob
from sys import argv


@dataclass
class Event:
    def __init__(self, start: datetime, end: datetime) -> None:
        """
        raises:
            ValueError if start >= end
        """
        if start > end:
            raise ValueError(f"The event ends before it starts! {start=} {end=}")
        self.start = start
        self.end = end
        self.next: Event = None # Next event in calendar

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.start=} {self.end=})"

class Calendar:
    def __init__(self, name: str, duration: datetime) -> None:
        split_by = "/" if "/" in name else "\\"
        self.name = name.split(split_by)[-1]
        self.events: list[Event] = []
        self.duration = duration
        "We are searching for an empty slot of such duration"

        self.last_checked: Event = None
        self.free_from: datetime = None
        """
        When CalendarSlotFinder checks if the calendar
        """
    
    def add_event(self, e: Event) -> None:
        """
        add an event to the calendar assuming it starts after the previous one ends
        raises:
            ValueError if the assumption is not met
        """
        if not self.events:
            self.events.append(e)
            return
        
        if self.events[-1].end > e.start:
            raise ValueError(f"The {e=} starts before the last event {self.events[-1]} {self.name}")

        self.events[-1].next = e
        self.events.append(e)

    def update_free_from(self, search_from: datetime) -> datetime:
        """
        free_from is the first datetime when there is a break in the calendar longer than duration
            but free_from is never before search_from
        returns:
            datetime: self.free_from
        """
        # calendar empty
        if not self.events:
            self.free_from = search_from
            return search_from


        if self.free_from:
            if (self.last_checked and self.last_checked.next
                and self.free_from + self.duration < self.last_checked.next.start):
                

                
            else:
                if self.free_from + self.duration > self.events[0].start:
                    return 


        # no last checked, but calendar not empty
        if self.last_checked is None:
            # there is free_time before the first event starts
            if self.events[0].start - search_from > self.duration:
                self.free_from = search_from
                return search_from
            # there is no time before the first event starts
            self.last_checked = self.events[0]

        # if free_from is set
        if self.free_from is not None:
            # if search_from is before free_from
            if search_from <= self.free_from:
                return self.free_from

            # if this is not the last event
            if self.last_checked.next is not None:
                # search_from is after free_from
                if search_from + self.duration <= self.last_checked.next.end:
                    self.free_from = search_from
                    return search_from



        if self.last_checked.next is not None:
            self.last_checked = self.last_checked.next
            while self.last_checked.next is not None:
                if self.last_checked.end + self.duration <= self.last_checked.next.start:
                    break
                self.last_checked = self.last_checked.next
        self.free_from = self.last_checked.end
        return self.free_from

    def how_much_free_time(self, search_from) -> timedelta:
        """
        Tells how much time the next break will have
        If there is no event next, then returns timedelta(hours=24*365.25*1000) -> thousand years.
        """
        inf = timedelta(hours=24 * 365.25 * 1000)
        if self.last_checked is None:
            if self.events:
                return self.events[0].start - search_from
            return inf
        
        if self.last_checked.next is None:
            return inf
        if self.last_checked.end < search_from:
            return self.last_checked.next.start - search_from
        return timedelta(days=0)



class CalendarsSlotFinder:
    def __init__(self, calendars_dir: str, min_people: int, duration_minutes: int, search_from: datetime) -> None:
        self.calendars_dir = calendars_dir
        self.calendars_file_names: list[str] = []

        self.min_people = min_people
        self.duration = timedelta(minutes=duration_minutes)
        self.search_from = search_from

        self.calendars: dict[str, Calendar] = {}

        # found calendar files?
        self.calendars_file_names: list[str] = self.find_calendar_files(calendars_dir)
        if not self.calendars_file_names:
            raise ValueError(f"No callendars were found under this directory: {calendars_dir = }")

        if len(self.calendars_file_names) < min_people:
            raise ValueError(f"Found only {len(self.calendars_file_names)} calendars, but there should be at least as many calendars as --minimum-people")

        self.load_calendars(self.find_calendar_files(self.calendars_dir))
    @staticmethod
    def find_calendar_files(calendars_dir) -> list[str]:
        path = f"{calendars_dir}*.txt"
        return glob(path)

    def load_calendars(self, file_names: list[str]) -> None:
        """
        Open files in calendars_dir
        """
        for name in file_names:
            self.calendars[name] = Calendar(name, self.duration)
            with open(name, "r", encoding="utf-8") as f:
                for line in f.read().split("\n"):
                    striped = line.strip()
                    if striped == "":
                        continue

                    # the whole day is full
                    if len(striped) == 10:
                        start = datetime.strptime(striped, '%Y-%m-%d')
                        self.calendars[name].add_event(Event(start, start + timedelta(hours=23, minutes=59, seconds=59)))
                        continue

                    # the duration of being busy is determined by two datetimes
                    begin = striped[:19]
                    end = striped[22:]
                    time_format = '%Y-%m-%d %H:%M:%S'
                    self.calendars[name].add_event(Event(
                        start=datetime.strptime(begin, time_format),
                        end=datetime.strptime(end, time_format)
                    ))

    def update_free_from_time_and_find_soonest_free_time(self, search_from: datetime) -> Calendar:
        soonest = Calendar("", timedelta(0))
        soonest.free_from = datetime(year=9999, month=9, day=9)
        for calendar in self.calendars.values():
            if calendar.update_free_from(search_from) < soonest.free_from:
                soonest = calendar
        return soonest

    def who_available_at(self, time_) -> list[Calendar]:
        who: list[Calendar] = []
        for calendar in self.calendars.values():
            if calendar.how_much_free_time(time_) >= self.duration:
                who.append(calendar)
        return who


    def find_available_slot(self) -> tuple[list[Calendar], datetime]:
        """
        pierwszy dostępny czas >= X
        kto jest dostępny na X od tego czasu
        czy to jest > n ludzi
        
        NIE
        jaki jest kolejny dostępny czas >= X
        kto jest dostępny na X od tego czasu
        czy to jest > n ludzi          
        """
        duration, search_from, min_people = self.duration, self.search_from, self.min_people
        # edge cases:
        if min_people < 1:
            raise ValueError("'n' has to be at least 1.")

        if len(self.calendars) < min_people:
            return [], None

        # find soonest available time >= X
        soonest_available_calendar: Calendar = self.update_free_from_time_and_find_soonest_free_time(search_from)
        print([cal.free_from.strftime("%Y-%m-%d %H:%M") for cal in self.calendars.values()])
        while True:
            # Who is available at this time
            who = self.who_available_at( soonest_available_calendar.free_from)
            if len(who) >= self.min_people:
                return who, soonest_available_calendar.free_from
            calendars = list(filter(lambda x: x.free_from > soonest_available_calendar.free_from, list(self.calendars.values())))
            calendars.sort(key=lambda cal: cal.free_from)
            print(soonest_available_calendar.name, [cal.name + " " + cal.free_from.strftime("%Y-%m-%d %H:%M") for cal in calendars])
            soonest_available_calendar = self.update_free_from_time_and_find_soonest_free_time(calendars[0].free_from)


if __name__ == "__main__":
    parser = ArgumentParser(description="Find first available slot for at least specified number of people.")
    parser.add_argument("--duration-in-minutes", type=int, required=True)
    parser.add_argument("--minimum-people", type=int, required=True)
    parser.add_argument("--calendars", type=str, required=True)
    #namespace = parser.parse_args(argv[1:])
    
    START = datetime(2022, 5, 15)
    #print(namespace.calendars, namespace.minimum_people, namespace.duration_in_minutes)
    #cals = CalendarsSlotFinder(namespace.calendars, namespace.minimum_people, namespace.duration_in_minutes, START)
    cals = CalendarsSlotFinder("task2-calendar\\in\\", 2, 100, START)
    calendars, time = cals.find_available_slot()
    #print(f"{calendars=} {time=}")
    print(", ".join([repr(c.name) for c in calendars]))
    print(time)
    for calendar in calendars:
        print(calendar.name, calendar.last_checked.end, "---", calendar.last_checked.next.start)




