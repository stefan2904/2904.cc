import sys
from icalendar import Calendar

if len(sys.argv) <= 1:
    print("Error: call this script with path to ical file in arguments")
    exit(1)

ical_file = sys.argv[1]

with open(ical_file, 'rb') as f:
    Calendar.ignore_exceptions = True
    try:
        # Attempt to parse the iCalendar file
        Calendar.from_ical(f.read())
        print('The iCalendar file is valid.')
        exit(0)
    except ValueError as e:
        # If the iCalendar file is invalid, catch the error and print the error message
        print('The iCalendar file is invalid:')
        print(e)
        exit(2)


