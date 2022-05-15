from __future__ import annotations

from dataclasses import dataclass, field
from sys import argv
from glob import glob
from argparse import ArgumentParser
from datetime import datetime, timedelta

#class Calendar:
#    def __init__(self, name: str, *busy: Duration) -> None:
#        self.name = name
#        self.busy = busy
#    
#    def busy_at(self, time: datetime) -> tuple[bool, timedelta]:
#        """
#        returns
#            bool: if busy at 'time' then True
#            timedelta: if not busy at 'time' then return how much time till busy
#        """

SECOND = timedelta(seconds=1)


@dataclass
class Busy:
    start: datetime 
    end: datetime
    next: Busy = field(default=None)

    def ended_by(self, time: datetime) -> bool:
        return self.end < time

@dataclass
class Calendar:
    name: str
    events: list[Busy] = field(default_factory=list)
    last_checked: Busy = field(default=None)

    def add_event(self, event: Busy) -> None:
        if self.events:
            self.events[-1].next = event
        self.events.append(event)

    def soonest_available_time(self, duration: timedelta, search_from: datetime) -> datetime:
        if len(self.events) == 0 or self.events[0].start - search_from >= duration:
            return search_from

        if self.last_checked is None:
            self.last_checked = self.events[0]
    
        while self.last_checked.next is not None:
            if self.last_checked.next.start - self.last_checked.end >= duration:
                return self.last_checked.end + SECOND
            self.last_checked = self.last_checked.next
        
        return self.last_checked.end + SECOND

    def is_free_at(self, duration: timedelta, start_time: datetime) -> bool:
        if not self.events:
            return True
        if self.last_checked is not None and self.last_checked.next is not None:
            return (self.last_checked.end
                        < start_time
                            < self.last_checked.next.start - duration)
        
        print("This should not be printed, because the is_free_at function should be called after the")
        return self.soonest_available_time(duration, start_time) < start_time



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
                        self.calendars[name].add_event(Busy(start, start + timedelta(hours=23, minutes=59)))
                        continue

                    # the duration of being busy is determined by two datetimes
                    begin = striped[:19]
                    end = striped[22:]
                    time_format = '%Y-%m-%d %H:%M:%S'
                    self.calendars[name].add_event(Busy(
                        start=datetime.strptime(begin, time_format),
                        end=datetime.strptime(end, time_format)
                    ))

    def soonest_available_time_users(self, duration: timedelta, search_from: datetime) -> tuple[str, datetime, dict[str, datetime]]:
        """
        returns:
            Tuple[
                str: who's calendar is this
                datetime: when is the available time
            ]
        """
        soonest: datetime = None
        soonest_name: str = None
        for name, cal in self.calendars.items():
            available = cal.soonest_available_time(duration, search_from)
            if soonest is None or available < soonest:
                soonest = available
                soonest_name = name

        return soonest_name, soonest

    def who_available_at(self, time: datetime, duration: timedelta) -> list[Calendar]:
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

        # pierwszy dostępny czas dłuuższy niż X
        # kto jest dostępny na X od tego czasu
        # czy to jest > n ludzi
        # 
        # NIE
        # jaki jest kolejny dostępny czas > X
        # kto jest dostępny na X od tego czasu
        # czy to jest > n ludzi  


        # edge cases:
        if n < 1:
            raise ValueError("'n' has to be at least 1.")

        if len(self.calendars) > n:
            return [], None

        # find soonest available time
        _, soonest_available = self.soonest_available_time_users(duration, search_from)
        found = False
        while not found:
            who = self.who_available_at(soonest_available, duration)
            if len(who) >= n:
                return who, soonest_available
            sorted(who, key=lambda cal: cal.last_checked.end)[0]
        return [], None


if __name__ == "__main__":
    parser = ArgumentParser(description="Find first available slot for at least specified number of people.")
    parser.add_argument("--duration-in-minutes", type=int, required=True)
    parser.add_argument("--minimum-people", type=int, required=True)
    parser.add_argument("--calendars", type=str, required=True)
    namespace = parser.parse_args(argv[1:])

    cale = namespace.calendars
    cale = cale[:-1] if cale[-1] == "/" else cale
    calendars_file_names = glob(f"{cale}/*.txt")

    cals = Calendars()
    cals.load_calendars(calendars_file_names)

    x = cals.find_available(timedelta(minutes=90), datetime(2022, 7, 1), 2)
    print(x)
#    for k, cal in cals.calendars.items():
#        print(k, cal.soonest_available_time(timedelta(minutes=30), datetime(2022, 7, 1)))
#        for d in cal.events:
#            print(f"\t{d}")

