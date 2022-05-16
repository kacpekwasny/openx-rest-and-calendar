from random import randint
from datetime import datetime, timedelta
from sys import argv
from tracemalloc import start

def generate(start_date: datetime, stop_date: datetime, event_max_hours=10, break_max_hours=12) -> list[list[datetime]]:
    events = []

    while start_date < stop_date:
        duration = timedelta(
            hours=randint(0, event_max_hours),
            minutes=randint(0, 59)
        )

        events.append(
            [start_date, start_date + duration]
        )

        # move start date by how long the event took place
        start_date += duration

        # make a break
        start_date += timedelta(
            hours=randint(0, break_max_hours),
            minutes=randint(0, 59)
        )
    return events

def calendar_to_string(calendar: list[list[datetime]]) -> str:
    return "\n".join([f"{t1} - {t2}" for t1, t2 in calendar])

if __name__ == "__main__":
    
    out = calendar_to_string(
            generate(
                datetime(2022, 5, 15),
                datetime(2022, 5, 30)))
    
    with open(argv[1], "w", encoding="utf-8") as f:
        f.write(out)

