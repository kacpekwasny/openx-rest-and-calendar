

### Example:

```bash
$ cd task2-calendar
$ python find-available-slot.py --duration-in-minutes 400 --minimum-people 5 --calendars /in/ --start "2022-05-14 22:12:13"
```

#### Manual:
```
usage: find-available-slot.py [-h] --duration-in-minutes DURATION_IN_MINUTES --minimum-people MINIMUM_PEOPLE --calendars CALENDARS [--start START]

Find first available slot for at least specified number of people.

options:
  -h, --help            show this help message and exit
  --duration-in-minutes DURATION_IN_MINUTES
                        Duration of slot in minutes
  --minimum-people MINIMUM_PEOPLE
                        Minimum people / calendars files have to have a free slot at the same time.
  --calendars CALENDARS
                        The directory, where the calendar files are. Ex.: '/in/', '.\in\'.
  --start START         Optional. Earliest time we will look for the beginning of the slot. Default is the current time.
```
