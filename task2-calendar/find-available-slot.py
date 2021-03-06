from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, timedelta
from glob import glob
from sys import argv

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

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
    def __init__(self, name: str, duration: datetime, start_time: datetime, events: list[Event]) -> None:
        split_by = "/" if "/" in name else "\\"
        self.name = name.split(split_by)[-1]

        self.events: list[Event] = []
        self.__add_events(start_time, events)
        self.last_checked: Event = self.events[0]

        self.duration = duration
        "We are searching for an empty slot of such duration"

        self.free_from: datetime = None
        "At this time there is at least a free slot of length of duration or longer"
    
    def __add_events(self, start_time: datetime, events: list[Event]) -> None:
        """
        add an events to the calendar assuming every one starts after the previous one ends
        raises:
            ValueError if the assumption is not met
        """
        if events:
            start_time = start_time if start_time < events[0].start else events[0].start
        prev = Event(datetime(1,1,1), start_time)
        self.events.append(prev)
        for e in events:
            if prev.end > e.start:
                raise ValueError(f"The {e=} starts before the last event {self.events[-1]} {self.name}")
            prev.next = e
            prev = e
            self.events.append(e)

    def update_free_from(self, search_from: datetime) -> datetime:
        """
        free_from is the first datetime when there is a break in the calendar longer than duration
            but free_from is never before search_from
        returns:
            datetime: self.free_from
        """

        # je??eli wiemy kiedy istnieje przerwa >= duration
        if self.free_from:
            
            # je??eli ta przerwa dopiero b??dzie
            if search_from < self.free_from:
                return self.free_from

            # je??eli to jest ostatni Event
            if self.last_checked.next is None:
                self.free_from = self.last_checked.end
                return self.free_from

            # je??eli ta przerwa ju?? si?? zacze??a
            if search_from + self.duration <= self.last_checked.next.start:
                self.free_from = search_from
                return self.free_from
            
            # przerwa si?? zacze??a, ale zosta??o w niej za ma??o czasu

        # trzeba przeszuka?? kolejne eventy czy pomi??dzy nimi jest przerwa
        while self.last_checked.next is not None:

            # je??eli przerwa mi??dzy ko??cem eventu a pocz??tkiem kolejnego jest przynajmniej d??ugo??ci duration
            if self.last_checked.end >= search_from and self.last_checked.next.start - self.last_checked.end >= self.duration:
                self.free_from = self.last_checked.end
                return self.free_from
            self.last_checked = self.last_checked.next

        self.free_from = self.last_checked.end
        return self.free_from

    def how_much_free_time(self, search_from) -> timedelta:
        """
        Tells how much time the next break will have
        If there is no event next, then returns timedelta(hours=24*365.25*1000) -> thousand years.
        """
        inf = timedelta(hours=24 * 365.25 * 1000)
        if self.last_checked.next is None:
            return inf
        if self.last_checked.end <= search_from:
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
            with open(name, "r", encoding="utf-8") as f:
                events: list[Event] = []
                for line in f.read().split("\n"):
                    striped = line.strip()
                    if striped == "":
                        continue

                    # the whole day is full
                    if len(striped) == 10:
                        start = datetime.strptime(striped, '%Y-%m-%d')
                        events.append(Event(start, start + timedelta(hours=23, minutes=59, seconds=59)))
                        continue

                    # the duration of being busy is determined by two datetimes
                    begin = striped[:19]
                    end = striped[22:]
                    time_format = '%Y-%m-%d %H:%M:%S'
                    events.append(Event(
                        start=datetime.strptime(begin, time_format),
                        end=datetime.strptime(end, time_format)
                    ))

            self.calendars[name] = Calendar(name, self.duration, self.search_from, events)

    def update_free_from_time_and_find_soonest_free_time(self, search_from: datetime) -> Calendar:
        soonest = Calendar("", timedelta(0), datetime(1,1,1), [])
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
        pierwszy dost??pny czas >= X
        kto jest dost??pny na X od tego czasu
        czy to jest > n ludzi
        
        NIE
        jaki jest kolejny dost??pny czas >= X
        kto jest dost??pny na X od tego czasu
        czy to jest > n ludzi          
        """
        search_from, min_people = self.search_from, self.min_people
        # edge cases:
        if min_people < 1:
            raise ValueError("'n' has to be at least 1.")

        if len(self.calendars) < min_people:
            return [], None

        # find soonest available time >= X
        soonest_available_calendar: Calendar = self.update_free_from_time_and_find_soonest_free_time(search_from)
        while True:
            # who is available at this time
            who = self.who_available_at( soonest_available_calendar.free_from)
            
            # is this at least the minimum number of people?
            if len(who) >= self.min_people:
                return who, soonest_available_calendar.free_from

            # calendars, that have free_from time later than the soonest_available_calendar.free_from
            calendars = list(filter(
                                lambda x: x.free_from > soonest_available_calendar.free_from,
                                self.calendars.values()
                            ))
            
            # sort the calendars to find first free_from time
            calendars.sort(key=lambda cal: cal.free_from)

            # all calendars are searched for the nearest free spot that starts after the new free_from
            soonest_available_calendar = self.update_free_from_time_and_find_soonest_free_time(calendars[0].free_from)


if __name__ == "__main__":
    parser = ArgumentParser(description="Find first available slot for at least specified number of people.")
    parser.add_argument("--duration-in-minutes", type=int, required=True, help="Duration of slot in minutes")
    parser.add_argument("--minimum-people", type=int, required=True, help="Minimum people / calendars files have to have a free slot at the same time.")
    parser.add_argument("--calendars", type=str, required=True, help="The directory, where the calendar files are. Ex.: '/in/', '.\\in\\'.")
    parser.add_argument("--start", type=str, required=False, default=datetime.now().strftime(DATETIME_FORMAT),
        help="Optional. Earliest time we will look for the beginning of the slot. Default is the current time.")

    namespace = parser.parse_args(argv[1:])
    cals = CalendarsSlotFinder(namespace.calendars,
                               namespace.minimum_people,
                               namespace.duration_in_minutes,
                               datetime.strptime(namespace.start, DATETIME_FORMAT))
    
    calendars, time = cals.find_available_slot()
    print(", ".join([repr(c.name) for c in calendars]))
    print(time)
    for calendar in calendars:
        print(calendar.name, calendar.last_checked.end, "---", calendar.last_checked.next.start if calendar.last_checked.next else "...")




