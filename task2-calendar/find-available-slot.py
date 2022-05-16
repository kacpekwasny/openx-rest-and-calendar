from __future__ import annotations

from dataclasses import dataclass, field
from sys import argv
from glob import glob
from argparse import ArgumentParser
from datetime import datetime, timedelta


SECOND = timedelta(seconds=1)


@dataclass
class Busy:
    start: datetime 
    end: datetime
    next: Busy = None


class Calendar:
    def __init__(self, name: str) -> None:
        self.name: str = name.split("\\")[-1]
        self.events: list[Busy] = []
        self.last_checked: Busy = None
        self.free_from: datetime = None

    def add_event(self, event: Busy) -> None:
        if self.events:
            self.events[-1].next = event
        self.events.append(event)

    def soonest_available_time(self, duration: timedelta, search_from: datetime) -> datetime:
        if len(self.events) == 0 or self.events[0].start - search_from >= duration:
            self.free_from = search_from
            return search_from

        if self.last_checked is None:
            self.last_checked = self.events[0]
    
        while self.last_checked.next is not None:
            if (self.last_checked.next.start - self.last_checked.end >= duration
                and self.last_checked.end >= search_from):
                self.free_from = self.last_checked.end + SECOND
                return self.free_from
            self.last_checked = self.last_checked.next
        
        self.free_from = self.last_checked.end + SECOND
        return self.free_from

    def is_free_at(self, duration: timedelta, start_time: datetime) -> bool:
        if not self.events:
            return True
        if self.last_checked is not None and self.last_checked.next is not None:
            return (self.last_checked.end
                        < start_time
                            < self.last_checked.next.start - duration)
        
        if self.last_checked.next is None:
            return True
        
        print("~~~~~~~~~ This should not be printed, because the is_free_at function should be called after the ~~~~~~~~~")
        return self.soonest_available_time(duration, start_time) < start_time

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name=} {self.free_from=})"


@dataclass
class Calendars:
    calendars: dict[str, Calendar] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Calendar:
        return self.calendars.get(key, default=None)

    def load_calendars(self, file_names: list[str]) -> Calendars:
        for name in file_names:
            self.calendars[name] = Calendar(name)
            with open(name, "r", encoding="utf-8") as f:
                for line in f.read().split("\n"):
                    striped = line.strip()
                    if striped == "":
                        continue

                    # the whole day is full
                    if len(striped) == 10:
                        start = datetime.strptime(striped, '%Y-%m-%d')
                        self.calendars[name].add_event(Busy(start, start + timedelta(hours=23, minutes=59, seconds=59)))
                        continue

                    # the duration of being busy is determined by two datetimes
                    begin = striped[:19]
                    end = striped[22:]
                    time_format = '%Y-%m-%d %H:%M:%S'
                    self.calendars[name].add_event(Busy(
                        start=datetime.strptime(begin, time_format),
                        end=datetime.strptime(end, time_format)
                    ))

    def update_soonest_available_time(self, duration: timedelta, search_from: datetime) -> Calendar:
        """
        For every calendar update soonest available time, and find the soonest
        returns:
            Calendar: 
        """
        soonest: Calendar = None
        for cal in self.calendars.values():
            available = cal.soonest_available_time(duration, search_from)
            if soonest is None or available < soonest.free_from:
                soonest = cal

        return soonest

    def who_available_at(self, duration: timedelta, time: datetime) -> list[Calendar]:
        who: list[str] = []
        for cal in self.calendars.values():
            if cal.is_free_at(duration, time):
                who.append(cal)
        return who

    def find_available(self, duration: timedelta, search_from: datetime, n: int) -> tuple[list[Calendar], datetime]:
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

        # pierwszy dostępny czas >= X
        # kto jest dostępny na X od tego czasu
        # czy to jest > n ludzi
        # 
        # NIE
        # jaki jest kolejny dostępny czas >= X
        # kto jest dostępny na X od tego czasu
        # czy to jest > n ludzi  


        # edge cases:
        if n < 1:
            raise ValueError("'n' has to be at least 1.")

        if len(self.calendars) < n:
            return [], None

        # find soonest available time >= X
        soonest_available_calendar = self.update_soonest_available_time(duration, search_from)
        while True:
            print(soonest_available_calendar)
            # Who is available at this time
            who = self.who_available_at(duration, soonest_available_calendar.free_from)
            print(who)
            if len(who) >= n:
                return who, soonest_available_calendar.free_from
            calendars = list(filter(lambda x: x.free_from > soonest_available_calendar.free_from, list(self.calendars.values())))
            calendars.sort(key=lambda cal: cal.free_from)
            soonest_available_calendar = self.update_soonest_available_time(duration, calendars[0].free_from)


if __name__ == "__main__":
    parser = ArgumentParser(description="Find first available slot for at least specified number of people.")
    parser.add_argument("--duration-in-minutes", type=int, required=True)
    parser.add_argument("--minimum-people", type=int, required=True)
    parser.add_argument("--calendars", type=str, required=True)
    namespace = parser.parse_args(argv[1:])
    
    
    pref = namespace.calendars
    path = f"{pref}*.txt"
    calendars_file_names = glob(path)

    cals = Calendars()
    cals.load_calendars(calendars_file_names)

    duration = timedelta(minutes=namespace.duration_in_minutes)
    start = datetime(2022, 5, 15)
    min_people = namespace.minimum_people
    print(f"{duration=} \n{start=} \n{min_people=}")
    calendars, time = cals.find_available(duration,
                                          start,
                                          min_people)
    print(", ".join([repr(c.name) for c in calendars]))
    print(time)

