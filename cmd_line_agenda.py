#!/usr/bin/env python3

from datetime import date, timedelta
import calendar
from enum import Enum
import os

AGENDA_PATH = 'agenda_stored.txt'
SETTINGS_PATH = 'user_settings.txt'

class TextColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TaskStatus(Enum):
    NOT_STARTED = 'NOT_STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'

class Agenda:

    '''
    Initializes a blank agenda.
    '''
    def __init__(self):
        # format of agenda dictionary:
        # {date: [(task description, task status), ...], ...}
        self.agenda = {}
        self.agenda[date.today()] = []

        # the date currently stored in the agenda that is farthest in the future
        self.farthest_date = date.today()

        # the date currently stored in the agenda that is farthest in the past
        self.earliest_date = date.today()

    '''
    Initializes an agenda from a representation stored in the given file path. If the file doesn't exist,
    creates a blank agenda instead.
    NOTE: dates must be stored in YYYY-MM-DD format.
    NOTE: agenda days must be separated by an empty line.
    NOTE: agenda tasks must be preceded by a string representation of the task status
    
    EXAMPLE AGENDA:
    2025-01-11
    DONE finish agenda application
    NOT_STARTED touch grass

    2025-01-12
    IN_PROGRESS software engineering homework

    PARAMS:
    file_path: string
    '''
    def __init__(self, file_path):
        self.agenda = {}
        self.farthest_date = date.today()
        self.earliest_date = date.today()

        if not os.path.isfile(file_path):
            self.agenda[date.today()] = []
            return

        with open(file_path, 'r') as f:
            split_into_days = f.read().strip().split('\n\n')
            for day_string in split_into_days:
                split_into_tasks = day_string.split('\n')

                # temporarily skips any days that don't have any tasks set for them
                # this will allow us to trim any excess days that are empty
                if len(split_into_tasks) == 1:
                    continue

                day_date = date.fromisoformat(split_into_tasks[0])
                self.agenda[day_date] = []

                for task in split_into_tasks[1:]:
                    task_tokenized = task.split()
                    self.agenda[day_date].append((' '.join(task_tokenized[1:]), TaskStatus(task_tokenized[0])))

                # keeps track of the farthest date stored
                if day_date > self.farthest_date:
                    self.farthest_date = day_date

                # keeps track of the earliest date stored
                if day_date < self.earliest_date:
                    self.earliest_date = day_date

        # ensures the agenda contains all days from today until the farthest day stored
        self._add_days(self.earliest_date, self.farthest_date)

    '''
    Saves this agenda to the given file path using the format described above.

    PARAMS:
    file_path: string
    '''
    def save(self, file_path):
        agenda_string = ''
        for day_date in self.agenda:
            agenda_string += day_date.isoformat() + '\n'
            for task, status in self.agenda[day_date]:
                agenda_string += status.value + ' ' + task + '\n'
            agenda_string += '\n'
        
        with open(file_path, 'w') as f:
            f.write(agenda_string.strip())

    '''
    Adds all the days from the specified start day to the specified end day to this agenda, inclusive
    of both end points, if they are not already present. Does not add any tasks to any days added.

    PARAMS:
    from_day: date
    to_day: date
    '''
    def _add_days(self, from_day, to_day):
        assert(to_day >= from_day)

        day_date = from_day
        while day_date <= to_day:
            if day_date not in self.agenda:
                self.agenda[day_date] = []
            day_date += timedelta(1)

    '''
    Returns a list of all the tasks for the given day, with each task represented as a
    tuple of its description and its status.

    PARAMS:
    day: date

    RETURNS:
    list(tuple(string, TaskStatus))
    '''
    def get_tasks(self, day):
        task_list = []
        for task_tuple in self.agenda[day]:
            task_list.append(task_tuple)
        return task_list

    '''
    Throws an error if a task with the given description already exists for the given day.
    '''
    def _check_not_duplicate(self, day, description):
        if description in [task[0] for task in self.agenda[day]]:
            raise Exception('Attempted to create duplicate task in day.')

    '''
    Adds a task with the given description and status to the task list for the given day.
    Also adds any intermediate days between the current farthest day stored and the given day,
    to ensure that the entire range of time in the agenda remains contiguous.

    The given description cannot be a duplicate of a description for another task for that day.

    PARAMS:
    day: date
    description: string
    status: TaskStatus

    THROWS:
    exception if a task with the same description already exists for that day
    '''
    def add_task(self, day, description, status):
        if day not in self.agenda:
            self.agenda[day] = []

        self._check_not_duplicate(day, description)

        self.agenda[day].append((description, status))
        if day > self.farthest_date:
            self._add_days(self.farthest_date, day)
            self.farthest_date = day

        self.refresh_today_date()

    '''
    Removes the task at the given index from the task list for the given day. Returns the task
    description that was removed and its status.

    PARAMS:
    day: date
    task_index: int

    RETURNS:
    string
    TaskStatus

    THROWS:
    exception if given day is not stored in agenda
    exception if given index is out of range
    '''
    def remove_task(self, day, task_index):
        assert(day in self.agenda)
        assert(task_index >= 0 and task_index < len(self.agenda[day]))
        old_description, old_status = self.agenda[day][task_index]
        self.agenda[day].remove((old_description, old_status))
        return old_description, old_status
    
    '''
    Changes the description of the task at the given index for the given day. Returns the
    original description for that task.

    The given description cannot be a duplicate of a description for another task for that day.

    PARAMS:
    day: date
    task_index: int
    new_description: string

    RETURNS:
    string

    THROWS:
    exception if a task with the same description already exists for that day
    exception if given day is not stored in agenda
    exception if given index is out of range
    '''
    def modify_task(self, day, task_index, new_description):
        assert(day in self.agenda)
        assert(task_index >= 0 and task_index < len(self.agenda[day]))
        self._check_not_duplicate(day, new_description)

        cur_description, cur_status = self.agenda[day][task_index]
        self.agenda[day][task_index] = (new_description, cur_status)

        return cur_description
        
    '''
    Changes the status of the task at the given index for the given day. Returns the
    original status for that task.

    PARAMS:
    day: date
    task_index: int
    new_status: TaskStatus

    RETURNS:
    TaskStatus

    THROWS:
    exception if given day is not stored in agenda
    exception if given index is out of range
    '''
    def update_task_status(self, day, task_index, new_status):
        assert(day in self.agenda)
        assert(task_index >= 0 and task_index < len(self.agenda[day]))
        cur_description, cur_status = self.agenda[day][task_index]
        self.agenda[day][task_index] = (cur_description, new_status)

        return cur_status

    '''
    Returns the date farthest in the future that is stored in this agenda.

    RETURNS:
    date
    '''
    def get_latest_date(self):
        return self.farthest_date

    '''
    Returns the date farthest in the past that is stored in this agenda.

    RETURNS:
    date
    '''
    def get_earliest_date(self):
        return self.earliest_date

    '''
    If today's date is not stored in the agenda for some reason (for example, if the day rolled over) then
    add it. This function should ideally be called just in case whenever the agenda needs to be displayed
    or when an important change should be made.
    '''
    def refresh_today_date(self):
        if date.today() not in self.agenda:
            self.agenda[date.today()] = []

        if self.farthest_date < date.today():
            self.farthest_date = date.today()
        elif self.farthest_date > date.today():
            self._add_days(date.today(), self.farthest_date)

    '''
    Just for debugging.
    '''
    def print_agenda(self):
        for date in self.agenda:
            pretty_print(date, TextColors.OKCYAN)
            index = 0
            for task, status in self.agenda[date]:
                pretty_print('0' + str(index) if index < 10 else str(index), TextColors.OKGREEN, end=' ')
                print(task)
                index += 1

class AgendaCommandLineInterface:

    '''
    Initializes an AgendaCommandLineInterface associated with the given agenda.

    PARAMS:
    agenda: Agenda
    additional_day_info: boolean
    '''
    def __init__(self, agenda):
        self.agenda = agenda

    def print_agenda(self, show_weekday=False, show_relative_to_today=False):
        print()
        pretty_print("--- YOUR AGENDA ---",  TextColors.BOLD)
        self.print_upcoming_days(show_weekday, show_relative_to_today)
        print()
        pretty_print("--- OVERDUE ITEMS ---", TextColors.BOLD)
        self.print_overdue()

    '''
    Pretty prints all the upcoming days stored in the associated agenda, separated initially and finally
    by an empty row. Starts from today and goes forward in time.
    '''
    def print_upcoming_days(self, show_weekday=False, show_relative_to_today=False):
        print()

        self.agenda.refresh_today_date()
        for day_date in date_range_inclusive(date.today(), self.agenda.get_latest_date()):

            # display what day of week it is
            if show_weekday:
                self._print_weekday(day_date)

            # display the date
            if day_date == date.today():
                pretty_print(day_date, TextColors.OKCYAN + TextColors.UNDERLINE, end='')
            else:
                pretty_print(day_date, TextColors.OKBLUE, end='')

            # display number of days after today
            if show_relative_to_today:
                self._print_relative_to_today(day_date)
            else:
                print()

            index = 0
            for task, status in self.agenda.get_tasks(day_date):
                if status == TaskStatus.DONE:
                    pretty_print('0' + str(index) if index < 10 else str(index), TextColors.OKGREEN, end=' ')
                    pretty_print('[D]', TextColors.OKGREEN, end=' ')
                    pretty_print(task, TextColors.OKGREEN)
                else:
                    pretty_print('0' + str(index) if index < 10 else str(index), TextColors.WARNING, end=' ')
                    pretty_print('[' + ('I' if status == TaskStatus.IN_PROGRESS else 'N') + ']', TextColors.WARNING, end=' ')
                    if status == TaskStatus.IN_PROGRESS:
                        pretty_print(task, TextColors.WARNING);
                    else:
                        print(task)
                index += 1

            print()

    '''
    Pretty prints the day of the week. This should be printed immediately before the date itself.

    PARAMS:
    day_date: date
    '''
    def _print_weekday(self, day_date):
        day_of_week = calendar.day_name[day_date.weekday()][:3].upper()
        pretty_print('[' + day_of_week + ']', TextColors.OKCYAN if day_date == date.today() else TextColors.OKBLUE, end=' ')

    '''
    Pretty prints the number of days after today corresponding to the given date. This should be printed
    immediately after the date itself.

    PARAMS:
    day_date: date
    '''
    def _print_relative_to_today(self, day_date):
        day_diff = (day_date - date.today()).days
        pretty_print(' [+' + str(day_diff) + ']', TextColors.OKCYAN if day_date == date.today() else TextColors.OKBLUE)

    '''
    Pretty prints all the past days stored in the associated agenda, separated initially and finally
    by an empty row. Starts from today and goes backward in time.
    '''
    def print_past_days(self):
        print()

        self.agenda.refresh_today_date()
        for day_date in date_range_inclusive(date.today(), self.agenda.get_earliest_date()):

            if day_date == date.today():
                pretty_print(day_date, TextColors.OKCYAN + TextColors.UNDERLINE)
            else:
                pretty_print(day_date, TextColors.HEADER)

            index = 0
            for task, status in self.agenda.get_tasks(day_date):
                if day_date == date.today():
                    if status == TaskStatus.DONE:
                        pretty_print('0' + str(index) if index < 10 else str(index), TextColors.OKGREEN, end=' ')
                        pretty_print('[D]', TextColors.OKGREEN, end=' ')
                        pretty_print(task, TextColors.OKGREEN)
                    else:
                        pretty_print('0' + str(index) if index < 10 else str(index), TextColors.WARNING, end=' ')
                        pretty_print('[' + ('I' if status == TaskStatus.IN_PROGRESS else 'N') + ']', TextColors.WARNING, end=' ')
                        print(task)
                else:
                    if status == TaskStatus.DONE:
                        pretty_print('0' + str(index) if index < 10 else str(index), TextColors.HEADER, end=' ')
                        pretty_print('[D]', TextColors.HEADER, end=' ')
                        pretty_print(task, TextColors.HEADER)
                    else:
                        pretty_print('0' + str(index) if index < 10 else str(index), TextColors.FAIL, end=' ')
                        pretty_print('[' + ('I' if status == TaskStatus.IN_PROGRESS else 'N') + ']', TextColors.FAIL, end=' ')
                        pretty_print(task, TextColors.FAIL)
                index += 1

            print()

    '''
    Pretty prints all the past days stored in the associated agenda, separated initially and finally
    by an empty row, that contain tasks that are not done. Starts from the earliest date and goes forward
    in time.
    '''
    def print_overdue(self):
        print()

        self.agenda.refresh_today_date()

        if (self.agenda.get_earliest_date() == date.today()):
            pretty_print("No overdue items!\n", TextColors.OKGREEN)
            return

        overdue_tasks = False

        for day_date in date_range_inclusive(self.agenda.get_earliest_date(), date.today() - timedelta(1)):
            index = 0

            outstanding_tasks = [task[1] for task in self.agenda.get_tasks(day_date) if task[1] != TaskStatus.DONE]

            if outstanding_tasks:
                overdue_tasks = True
                pretty_print(day_date, TextColors.FAIL)
            
            for task, status in self.agenda.get_tasks(day_date):
                if status != TaskStatus.DONE:
                    pretty_print('0' + str(index) if index < 10 else str(index), TextColors.FAIL, end=' ')
                    pretty_print('[' + ('I' if status == TaskStatus.IN_PROGRESS else 'N') + ']', TextColors.FAIL, end=' ')
                    pretty_print(task, TextColors.FAIL)
                index += 1

            if outstanding_tasks:
                print()

        if not overdue_tasks:
            pretty_print("No overdue items!\n", TextColors.OKGREEN)

    '''
    Pretty prints a welcome message.
    '''
    def print_welcome(self):
        print()
        pretty_print("COMMAND-LINE AGENDA APPLICATION", TextColors.OKCYAN + TextColors.UNDERLINE)
        pretty_print("Made by Dustin Zhang for personal use, 2025-01-11.", TextColors.OKCYAN)

    '''
    Pretty prints the instructions.
    '''
    def print_instructions(self):
        pretty_print("\nINSTRUCTIONS\n", TextColors.UNDERLINE)
        pretty_print("Press [ENTER] without typing anything to view your agenda.", TextColors.WARNING)
        pretty_print("Type 'vu' to view all upcoming days.", TextColors.WARNING)
        pretty_print("Type 'vp' to view all past days.", TextColors.WARNING)
        pretty_print("Type 'vl' to view all late tasks.\n", TextColors.WARNING)
        pretty_print("Type 'a' followed by a YYYY-MM-DD date and a text description to add a NOT_STARTED task to that day.", TextColors.WARNING)
        pretty_print("Type 'r' followed by a YYYY-MM-DD date and the index of a task, to remove that task from that day.", TextColors.WARNING)
        pretty_print("Type 'm' followed by a YYYY-MM-DD date, the index of a task, and a text description to rename that task.", TextColors.WARNING)
        pretty_print("Type 'u' followed by a YYYY-MM-DD date and the index of a task to cycle its status through NOT_STARTED, IN_PROGRESS, and DONE.\n", TextColors.WARNING)
        pretty_print("Type 's' to save all changes. REMEMBER TO DO THIS! Otherwise your changes may be lost when you close the program.", TextColors.WARNING)
        pretty_print("Type 'sq' to save and quit, or 'q'/'quit' to quit without saving.", TextColors.WARNING)
        pretty_print("Type 'o' to open a settings menu.", TextColors.WARNING)
        pretty_print("Type 'help' to view these instructions.\n", TextColors.WARNING)
        pretty_print("Some (possibly) helpful notes:\n", TextColors.BOLD)
        pretty_print("[N] means NOT_STARTED, [I] means IN_PROGRESS, and [D] means DONE.\n", TextColors.WARNING)
        pretty_print("Whenever you need to type a date, you can instead type:", TextColors.WARNING)
        pretty_print("*   \"today\" or \"now\" for today's date", TextColors.WARNING)
        pretty_print("*   \"+N\" where N is a number of days after today (e.g. \"+7\" means one week from today's date)", TextColors.WARNING)
        print()

    '''
    Pretty prints the settings menu.
    '''
    def print_settings_menu(self):
        pretty_print("\nSETTINGS\n", TextColors.UNDERLINE)
        pretty_print("Press [ENTER] without typing anything to exit the menu.", TextColors.WARNING)
        pretty_print("Press the corresponding key to toggle a setting.", TextColors.WARNING)
        pretty_print("[0] Toggle cool setting", TextColors.WARNING)
        pretty_print("[1] Display the day of the week next to each date", TextColors.WARNING)
        pretty_print("[2] Display the number of days after today corresponding to each date", TextColors.WARNING)
        print()


    '''
    Pretty prints a prompt for the user to enter a command.
    '''
    def prompt_next_command(self):
        print("*************************\n\n\nEnter next command: ", end='')

    '''
    Pretty prints if the command entered by the user was not recognized.
    '''
    def invalid_command(self):
        print("Command not recognized.")

    '''
    Pretty prints agenda save confirmation.
    '''
    def save_successful(self):
        print("Agenda saved to " + AGENDA_PATH + ".")

    '''
    Pretty prints agenda item added confirmation.
    '''
    def add_item_successful(self, day, description):
        print(f"Successfully added task \"{description}\" under {day}.")

    '''
    Pretty prints agenda item removed confirmation.
    '''
    def remove_item_successful(self, day, description):
        print(f"Successfully removed task \"{description}\" from {day}.")

    '''
    Pretty prints agenda item description modified confirmation.
    '''
    def modify_item_successful(self, day, old_description, new_description):
        print(f"Successfully updated description of task from \"{old_description}\" to \"{new_description}\" under {day}.")

    '''
    Pretty prints agenda item status updated confirmation.
    '''
    def update_status_item_successful(self, day, description, old_status, new_status):
        print(f"Successfully updated status of task \"{description}\" from \"{old_status}\" to \"{new_status}\" under {day}.")

    '''
    Pretty prints an error message.
    '''
    def error(self, error_message):
        print("Something went wrong, sorry!")
        pretty_print(error_message, TextColors.FAIL)

    '''
    Pretty prints user quit without saving confirmation.
    '''
    def quit_confirmation(self):
        pretty_print("Are you sure you want to quit? Your changes will not be saved. (y/n) ", TextColors.WARNING, end='')

    '''
    Pretty prints a little goodbye message.
    '''
    def goodbye(self):
        pretty_print("Goodbye!", TextColors.WARNING)

    '''
    Pretty prints a prompt for the user to change a setting if the user is in the settings menu.
    '''
    def prompt_next_settings_command(self):
        print("\nEnter a setting to change (leave blank to exit settings menu): ", end='')

    '''
    Pretty prints confirmation that a user changed a setting.
    '''
    def confirm_setting_changed(self, setting_name, new_value):
        pretty_print(f"Changed setting \"{setting_name}\" to {new_value}.", TextColors.WARNING)

    '''
    Pretty prints confirmation that any updated settings have been saved.
    '''
    def confirm_settings_saved(self):
        pretty_print(f"Settings saved to {SETTINGS_PATH}.", TextColors.WARNING)


class AgendaCommandLineController:

    class Menu(Enum):
        MAIN = 0
        SETTINGS = 1

    '''
    Initializes an AgendaCommandLineController that handles the given agenda and the given command
    line interface. The agenda and the view need to already been associated with each other.

    NOTE: all commands are stored in the commands dictionary and maps to a command function. Every
    command function takes in one additional argument, which is a list of string arguments for that
    command. How those arguments are parsed depends on the syntax of the command.

    PARAMS:
    agenda: Agenda
    view: AgendaCommandLineInterface
    '''
    def __init__(self, agenda, view):
        self.agenda = agenda 
        self.agenda_view = view 
        self.cur_menu = AgendaCommandLineController.Menu.MAIN

        # maps each command to a particular function to be called
        # each function must take in a list of arguments
        self.commands = {
            'vu': self.view_upcoming,
            'vp': self.view_past,
            'vl': self.view_overdue,
            'help': self.view_help,
            's': self.save_agenda,
            'a': self.add_item,
            'r': self.remove_item,
            'm': self.update_description_item,
            'u': self.update_status_item,
            'o': self.view_settings,
        }

        # maps each settings command to the index of the setting it should change
        self.settings_commands = {
            '0': 0,
            '1': 1,
            '2': 2,
        }

        self.settings_names = [
            "random setting",
            "show weekday names",
            "show number of days from today",
        ]

        if os.path.isfile(SETTINGS_PATH):
            try:
                self._load_saved_settings()
            except:
                # strictly speaking this should be in the view but oh well
                pretty_print("\nWARNING: Failed to load saved user settings from disk. Settings have been temporarily reset to default and will be saved when they are next modified.", TextColors.FAIL)
                self._reset_all_settings()
        else:
            self._reset_all_settings()

    '''
    Resets all user settings to their default values.
    '''
    def _reset_all_settings(self):
        self.settings_list = [
            False,
            False,
            False,
        ]

    def view_agenda(self, args):
        self.agenda_view.print_agenda(self.settings_list[1], self.settings_list[2])
    
    def view_upcoming(self, args):
        self.agenda_view.print_upcoming_days(self.settings_list[1], self.settings_list[2])

    def view_past(self, args):
        self.agenda_view.print_past_days()

    def view_overdue(self, args):
        self.agenda_view.print_overdue()

    def view_help(self, args):
        self.agenda_view.print_instructions()

    def save_agenda(self, args):
        self.agenda.save(AGENDA_PATH)
        self.agenda_view.save_successful()

    def add_item(self, args):
        day_date = self._parse_date(args[0])
        description = ' '.join(args[1:])
        self.agenda.add_task(day_date, description, TaskStatus.NOT_STARTED)
        self.agenda_view.add_item_successful(day_date, description)

    def remove_item(self, args):
        day_date = self._parse_date(args[0])
        index = int(args[1])
        self.agenda_view.remove_item_successful(day_date, self.agenda.remove_task(day_date, index)[0])

    def update_description_item(self, args):
        day_date = self._parse_date(args[0])
        index = int(args[1])
        description = ' '.join(args[2:])
        self.agenda_view.modify_item_successful(day_date, self.agenda.modify_task(day_date, index, description), description)

    def update_status_item(self, args):
        next_enum = {
            TaskStatus.NOT_STARTED: TaskStatus.IN_PROGRESS,
            TaskStatus.IN_PROGRESS: TaskStatus.DONE,
            TaskStatus.DONE: TaskStatus.NOT_STARTED,
        }

        day_date = self._parse_date(args[0])
        index = int(args[1])
        old_status = self.agenda.get_tasks(day_date)[index][1]
        self.agenda.update_task_status(day_date, index, next_enum[old_status])
        description, new_status = self.agenda.get_tasks(day_date)[index]
        self.agenda_view.update_status_item_successful(day_date, description, old_status.value, new_status.value)

    '''
    Called when the user brings up the settings menu.

    PARAMS:
    args: list(string)
    '''
    def view_settings(self, args):
        self.agenda_view.print_settings_menu()
        self.cur_menu = AgendaCommandLineController.Menu.SETTINGS

    '''
    Called when the user toggles the setting in the settings list at the given index in the list.

    PARAMS:
    index: int
    '''
    def settings_toggle_setting(self, index):
        self.settings_list[index] = not self.settings_list[index]
        self.agenda_view.confirm_setting_changed(self.settings_names[index], str(self.settings_list[index]).upper())

    '''
    Called when the user closes out of the settings menu, saving all the current user settings.

    PARAMS:
    args: list(string)
    '''
    def settings_save(self, args):
        with open(SETTINGS_PATH, 'w') as f:
            for i in range(len(self.settings_names)):
                f.write(self.settings_names[i] + ": " + str(self.settings_list[i]) + "\n")
        self.agenda_view.confirm_settings_saved()

    '''
    Loads any saved user settings from disk, if there are any.
    NOTE: this function does not check whether the file exists already.
    NOTE: the settings are saved in a text file where each line has the following format:
    <setting name/description> <value>

    Example:
    additional day information: True
    '''
    def _load_saved_settings(self):
        with open(SETTINGS_PATH, 'r') as f:
            self.settings_list = []
            lines = f.readlines()

            # currently only boolean values for settings are supported
            for i in range(len(lines)):
                description, setting = lines[i].strip().split(": ")
                assert(description == self.settings_names[i])
                assert(setting == str(True) or setting == str(False) or setting.isdigit())
                if setting == str(True):
                    self.settings_list.append(True)
                elif setting == str(False):
                    self.settings_list.append(False)
                else:
                    raise Exception("Unknown format for setting value.")

    '''
    Checks whether the given string is one of the alternatives the user can write instead of
    putting in a date. If so, returns the date that corresponds to that alternative. For example, if
    today's date is 2025-01-11 and the string is "today", returns 2025-01-11. Otherwise, attempts
    to parse that string as a date.

    PARAMS:
    date_string: string

    RETURNS:
    date
    '''
    def _parse_date(self, date_string):

        # the user can write "today" or "now" instead of today's date
        if date_string in ('today', 'now'):
            return date.today()

        # the user can write +N where N is a number of days after today
        elif '+' in date_string:
            return date.today() + timedelta(int(date_string.split('+')[1]))

        return date.fromisoformat(date_string)

    '''
    Handles any commands when the user is on the main loop. Before this function is called, check that
    the user is currently on the main loop (and not on another menu like the settings menu).

    Returns:
    boolean: True if the user will continue using the application, False if the user input a quit command
    '''
    def _handle_main_loop(self):
        self.agenda_view.prompt_next_command()
        command = input()

        # handles a couple special commands
        if not command:
            self.view_agenda([])
            return False
        elif command == "sq":
            self.save_agenda([])
            return True
        elif command == "quit" or command == 'q':
            confirmation = ''
            while not confirmation in ('y', 'n'):
                self.agenda_view.quit_confirmation()
                confirmation = input()
            if confirmation == 'y':
                return True 
            else:
                return False

        # other commands are all stored in the commands dictionary
        # TODO: abstract this out with the settings menu handler
        command_list = command.split()
        if command_list[0] not in self.commands:
            self.agenda_view.invalid_command()
            return False 
            
        try:
            self.commands[command_list[0]](command_list[1:])
        except Exception as e:
            self.agenda_view.error(str(e))

        return False

    '''
    Handles any commands when the user is on the settings menu. Before this function is called, check that
    the user is currently on the settings menu.

    Returns:
    boolean: True if the user will continue using the application, False if the user input a quit command
    '''
    def _handle_settings_menu(self):
        self.agenda_view.prompt_next_settings_command()
        command = input()

        # handles a couple special commands
        if not command:
            self.settings_save([])
            self.cur_menu = AgendaCommandLineController.Menu.MAIN
            return False

        # other settings options are all stored in the settings dictionary
        # TODO: abstract this out with the main loop handler
        command_list = command.split()
        if command_list[0] not in self.settings_commands:
            self.agenda_view.invalid_command()
            return False 
            
        try:
            self.settings_toggle_setting(self.settings_commands[command_list[0]])
        except Exception as e:
            self.agenda_view.error(str(e))

        return False

    '''
    Runs the controller.
    '''
    def go(self):
        self.agenda_view.print_welcome()
        self.agenda_view.print_instructions()

        while True:
            user_quit = False
            if self.cur_menu == AgendaCommandLineController.Menu.SETTINGS:
                self._handle_settings_menu()
            else:
                user_quit = self._handle_main_loop()
            
            if user_quit:
                break

        self.agenda_view.goodbye()

'''
Prints the given string using the given color.

PARAMS:
text: string
color: TextColors.color
'''
def pretty_print(text, color, end='\n'):
    print(f'{color}{text}{TextColors.ENDC}', end=end)

'''
Returns a list containing all the dates from the start date to the end date, in increasing order if
the start date is less than the end date and in decreasing order otherwise. The list includes both the
start date and the end date.

PARAMS:
start_date: date
end_date: date

RETURNS:
list(date)
'''
def date_range_inclusive(start_date, end_date):
    l = [start_date]
    if start_date <= end_date:
        while l[-1] < end_date:
            l.append(l[-1] + timedelta(1))
    else:
        while l[-1] > end_date:
            l.append(l[-1] - timedelta(1))
    return l

def main():
    agenda = Agenda(AGENDA_PATH)
    agenda_view = AgendaCommandLineInterface(agenda)
    agenda_controller = AgendaCommandLineController(agenda, agenda_view)
    agenda_controller.go()

if __name__ == '__main__':
    main()