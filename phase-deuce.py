#!/usr/bin/env python3
#
# phase-deuce
# https://github.com/gregkrsak/phase-deuce
#
# Automatically populates a random daily log of customers for businesses offering table service.
# Inspired by Phase 2 of WA State Governor Inslee's COVID-19 reopening plan. Of course, this is
# to be used for testing purposes only!
#
# Copyright (c) 2020 Greg M. Krsak (greg.krsak@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# Required for io.StringIO()
import io
# Required for .CSV file operations
import csv
# Required for datetime.date()
import datetime
# Required for zlib.adler32()
import zlib
# Required for standard input/output routines
import sys
# Required for atexit.register()
import atexit
# Required for time.time()
import time
# Required for random number generation
import random
# Required for regular expressions
import re


# Constants used for logging
LOG_LEVEL_DEBUG = 1
LOG_LEVEL_INFO = 2
LOG_LEVEL_WARN = 3
LOG_LEVEL_ERROR = 4
LOG_LEVEL_SYSTEM = 5
LOG_LEVEL_NONE = 100
# Constants used for identity indexing
ID_NAME = 0
ID_EMAIL = 1
ID_PHONE = 2
# Constants used for Operating System detection
OS_WINDOWS = 1
OS_NON_WINDOWS = 2


def init(argv):
    """
    This is the code block that is run on startup.
    :return: None
    """
    detect_os()
    app = Application()
    app.run()
    return


def detect_os():
    """
    A rudamentary way to detect whether we are on Windows or a non-Windows operating system.
    """
    result = OS_NON_WINDOWS
    try:
        import termios
    except ImportError:
        result = OS_WINDOWS
    return result


def _find_getch():
    """
    Determines the OS-specific function to return a keypress.
    Ref: https://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user
    """
    if detect_os() == OS_NON_WINDOWS:
        # POSIX
        import termios
    else:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty

    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch


##########################################################################################
## Abstract classes                                                                     ##
##########################################################################################


class Model:
    """
    An abstract MVC model.
    """
    def __init__(self, view):
        self.view = view


class View:
    """
    An abstract MVC view.
    """
    def __init__(self, output_stream):
        self.buffer = io.StringIO()
        self.output = output_stream

    def waiting_output(self):
        result = self.buffer.getvalue()
        self.buffer.truncate(0)
        return result

    def update(self):
        """
        Flush the output buffer.
        """
        self.output.write(self.waiting_output())


class Controller:
    """
    An abstract MVC controller.
    """
    def __init__(self):
        self.model = Model()
        self.view = View()


##########################################################################################
## Main program classes                                                                 ##
##########################################################################################


class Application(Controller):
    """
    The primary application code for the phase-deuce program.
    :return: None
    """

    def __init__(self):
        atexit.register(self.shutdown)
        self.startup()
        pass

    def startup(self):
        """
        Performs tasks for the Application instance that should happen on startup.
        """
        # Initialize the internal logger (unrelated to writing to .CSV files)
        self.log = Log(LOG_LEVEL_DEBUG)
        # Determine the proper (OS-specific) function to get keypresses
        self.getch = _find_getch()

        result = True
        try:
            # Initialize the random number generator
            random.seed()
            # Initialize the primary MVC view
            self.view = Screen()
            # Initialize the primary MVC model
            self.model = Database(self.log)
        except:
            # Was an exception thrown?
            result = False

        self.log.system(result, 'Application startup')
        return

    def run(self):
        """
        Runs the Application instance.
        """
        the_user_still_wants_to_run_this_application = True
        self.log.info('Welcome to phase-deuce')
        self.log.info('Written by Greg M. Krsak (greg.krsak@gmail.com)')
        self.log.info('Contribute or file bugs here: https://github.com/gregkrsak/phase-deuce')
        self.log.info('Press SPACE to add a new log entry. Press Q or X or CTRL-C to exit.')

        while the_user_still_wants_to_run_this_application:
            # Get a keypress from the user.
            if detect_os() == OS_NON_WINDOWS:
                user_input = self.getch()
            else:
                user_input = str(self.getch(), 'utf-8')
            self.log.debug('self.getch() == ' + user_input)
            # Did the user press SPACEBAR?
            if user_input == ' ':
                # Add a new row to the database
                db_write_succeeded = self.model.create_row()
                self.log.system(db_write_succeeded, 'Log entry written')
            # Did the user press Q or X or CTRL-C?
            elif user_input.upper() == 'Q' or user_input.upper() == 'X' or user_input == '\x03':
                # Exit
                the_user_still_wants_to_run_this_application = False

        return

    def shutdown(self):
        """
        Performs tasks for the Application instance that should happen on shutdown.
        """
        result = True
        try:
            pass # Do nothing
        except:
            # Was an exception thrown?
            result = False
        self.log.system(result, 'Application shutdown')
        return


class Database(Model):
    """
    This class performs database operations on .CSV files.
    The filename format is: phase-deuce-log_YYYY-MM-DD.csv
    The row format is: unix_time,full_name,email_address,phone_number,checksum
    """

    empty_string = ''
    delimiter_string = ','
    quote_string = '"'

    encoding = 'utf-8'

    filename_prefix = 'phase-deuce-log_'
    filename_suffix = '.csv'

    column_unix_time = 0
    column_full_name = 1
    column_email_address = 2
    column_phone_number = 3
    column_checksum = 4

    def __init__(self, log):
        super().__init__(log)

    def todays_filename(self):
        """
        Calculates today's filename string using the ISO 8601 format date.
        :return: A string with the format "phase-deuce-log_YYYY-MM-DD.csv".
        """
        date_string = datetime.date.today().isoformat()
        result = Database.filename_prefix + date_string + Database.filename_suffix
        return result

    def validate(self, filename=None):
        """
        Validates today's .CSV file.
        :return: True or False, depending on if the validation was successful.
        """
        # Figure out the filaname
        if not filename:
            filename = self.todays_filename()
        # Default to success
        result = True
        try:
            with open(filename, 'r', newline=Database.empty_string) as file:
                db = csv.reader(file,
                                delimiter=Database.delimiter_string,
                                quotechar=Database.quote_string)
                # Iterate over each row
                for row in db:
                    # Create a string from the joined list items of this row
                    row_string = Database.delimiter_string.join(row)
                    # Create the string to validate via checksum
                    string_to_validate = row[Database.column_unix_time] \
                                        + row[Database.column_full_name] \
                                        + row[Database.column_email_address] \
                                        + row[Database.column_phone_number]
                    # Create a binary encoded representation of that same string
                    bytes_to_validate = string_to_validate.encode(encoding=Database.encoding)
                    # Calculate checksum and read the existing checksum
                    fresh_checksum = zlib.adler32(bytes_to_validate)
                    existing_checksum = int(row[Database.column_checksum])
                    # Fail if any row's checksum does not match
                    if (fresh_checksum != existing_checksum):
                        result = False
        except:
            # Was an exception thrown?
            result = False
        return result


    def create_row(self):
        """
        Creates a database row that's populated with fake personally-identifying data.
        Note that the columns 'unix_time' and 'checksum' will be valid.
        :return: True or False, depending on if the write is considered successful.
        """
        filename = self.todays_filename()
        # Default to success
        result = True
        try:
            with open(filename, 'a', newline=Database.empty_string) as file:
                db = csv.writer(file,
                                delimiter=Database.delimiter_string,
                                quotechar=Database.quote_string)
                # Get the current UNIX time
                unix_time = int(time.time())
                # Create the fake person
                identity = PersonGenerator.new_identity()
                # Prepare the data to be validated later via checksum
                string_to_validate = str(unix_time) \
                                    + identity[ID_NAME] \
                                    + identity[ID_EMAIL] \
                                    + identity[ID_PHONE]
                bytes_to_validate = string_to_validate.encode(encoding=Database.encoding)
                # Calculate the checksum
                checksum = zlib.adler32(bytes_to_validate)
                # Write the row data to the .CSV file
                row = [unix_time, identity[ID_NAME], identity[ID_EMAIL], identity[ID_PHONE], checksum]
                db.writerow(row)
            # Re-validate the database after the write
            result = self.validate(filename)
        except:
            # Was an exception thrown?
            result = False
        return result


class Screen(View):
    """
    Represents the stdout stream.
    """

    eol = '\n'

    def __init__(self):
        super().__init__(sys.stdout)
        if detect_os() == OS_WINDOWS:
            Screen.eol = '\r\n'


class Log(Screen):
    """
    This class logs application events to the screen.
    """

    eol = Screen.eol

    prefix_braces = ['[ ', ' ]']
    prefix_separator = '  '
    system_ok_string = 'OK'
    system_fail_string = 'FAIL'
    debug_string = 'DEBUG'
    info_string = 'INFO'
    warn_string = 'WARN'
    error_string = 'ERROR'

    def __init__(self, level):
        super().__init__()
        self.level = level

    def system(self, status, message):
        if self.level <= LOG_LEVEL_SYSTEM:
            if status == True:
                self.__printlog(self.system_ok_string, message)
            else:
                self.__printlog(self.system_fail_string, message)

    def debug(self, message):
        if self.level <= LOG_LEVEL_DEBUG:
            self.__printlog(self.debug_string, message)

    def info(self, message):
        if self.level <= LOG_LEVEL_INFO:
            self.__printlog(self.info_string, message)

    def warn(self, message):
        if self.level <= LOG_LEVEL_WARN:
            self.__printlog(self.warn_string, message)

    def error(self, message):
        if self.level <= LOG_LEVEL_ERROR:
            self.__printlog(self.error_string, message)

    def __printlog(self, prefix_string, message):
        self.buffer.write(self.prefix_braces[0] + prefix_string + self.prefix_braces[1] \
                        + self.prefix_separator + message + Log.eol)
        self.update()


class PersonGenerator():
    """
    This is a static class used to generate pseudo-random "personal info".
    I was pretty tired when I wrote this, so forigve me if it looks like a giant hack.
    """

    __first_names = ['Robert', 'Shawn', 'William', 'James', 'Oliver', 'Benjamin', \
                    'Elijah', 'Lucas', 'Dick', 'Logan', 'Alexander', 'Ethan', \
                    'Jacob', 'Michael', 'Daniel', 'Henry', 'Jackson', 'Sebastian', \
                    'Peter', 'Matthew', 'Samuel', 'David', 'Joseph', 'Carter', \
                    'Mary', 'Patricia', 'Linda', 'Barbara', 'Elizabeth', 'Jennifer', \
                    'Maria', 'Susan', 'Margaret', 'Dorothy', 'Lisa', 'Nancy', \
                    'Karen', 'Betty', 'Helen', 'Sandra', 'Donna', 'Carol', \
                    'Ruth', 'Sharon', 'Michelle', 'Laura', 'Sarah', 'Kimberly']
    __last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', \
                    'Davis', 'Wilson', 'Anderson', 'Taylor', 'Moore', 'Thomas', \
                    'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Garcia', \
                    'Martinez', 'Robinson', 'Clark', 'Rodriguez', 'Lewis', 'Lee', \
                    'Walker', 'Hall', 'Allen', 'Young', 'Hernandez', 'King', \
                    'Wang', 'Devi', 'Zhang', 'Li', 'Liu', 'Singh', \
                    'Yang', 'Kumar', 'Wu', 'Xu']
    __email_domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'icloud.com', 'aol.com', 'mail.com']

    def new_identity():
        # Initialize an empty list to store the result
        result = ['', '', '']
        # Calculate the length of the name lists
        first_names_len = len(PersonGenerator.__first_names)
        last_names_len = len(PersonGenerator.__last_names)
        # Choose a random first and last name
        first_names_index = random.randrange(0, first_names_len)
        last_names_index = random.randrange(0, last_names_len)
        first_name = PersonGenerator.__first_names[first_names_index]
        last_name = PersonGenerator.__last_names[last_names_index]
        # Build the new name
        result[ID_NAME] = first_name + ' ' + last_name
        # Build the new email address
        result[ID_EMAIL] = PersonGenerator.__generate_email(first_name, last_name)
        # Build the new phone number
        result[ID_PHONE] = PersonGenerator.__generate_phone_number()

        return result

    def __generate_email(first_name, last_name):
        # Email style constants
        STYLE_FIRST_DOT_LAST = 0
        STYLE_LAST_DOT_FIRST = 1
        STYLE_FIRST_LAST = 2
        STYLE_F_LAST = 3
        # Select a random email style
        style = random.randrange(STYLE_FIRST_DOT_LAST, STYLE_F_LAST + 1)
        # Make the first and last names lowercase
        first_name = first_name.lower()
        last_name = last_name.lower()
        # Calculate the length of the email domain list
        email_domains_len = len(PersonGenerator.__email_domains)
        # Choose a random email domain
        email_domains_index = random.randrange(0, email_domains_len)
        domain_name = PersonGenerator.__email_domains[email_domains_index]
        # Format the email username
        if style == STYLE_FIRST_DOT_LAST:
            username = first_name + '.' + last_name
        elif style == STYLE_LAST_DOT_FIRST:
            username = last_name + '.' + first_name
        elif style == STYLE_FIRST_LAST:
            username = first_name + last_name
        elif style == STYLE_F_LAST:
            username = first_name[0] + last_name
        # Return the finished email address
        result = username + '@' + domain_name
        return result

    def __generate_phone_number():
        # This regex validates a 10-digit telephone number
        # Ref: https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch04s02.html
        nanp_regex = re.compile('^\(?([2-9][0-8][0-9])\)?[-.]?([2-9][0-9]{2})[-.]?([0-9]{4})$')
        # Generate random phone numbers until we get one that's valid according to the NANP
        phone_number_is_invalid = True
        while phone_number_is_invalid:
            result = str(PersonGenerator.__generate_npa()) + '-' \
                        + str(PersonGenerator.__generate_nxx()) + '-' \
                        + str(PersonGenerator.__generate_xxxx())
            if nanp_regex.match(result):
                phone_number_is_invalid = False
        return result

    def __generate_npa():
        result = random.randrange(0, 1000)
        return result

    def __generate_nxx():
        result = random.randrange(0, 1000)
        return result

    def __generate_xxxx():
        result = random.randrange(0, 10000)
        return result


##########################################################################################
## Bootstrap                                                                            ##
##########################################################################################


# Bootstraps the application via the init() function
if __name__ == '__main__':
    argv = ''
    try:
        argv = sys.argv[1]
    except:
        pass
    init(argv)

# End of phase-deuce.py
