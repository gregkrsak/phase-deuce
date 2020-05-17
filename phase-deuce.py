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


# Required for .CSV file operations
import csv
# Required for datetime.date()
import datetime
# Required for zlib.adler32()
import zlib
# Required for sys.argv, keyboard input, sys.exc_info(), sys.exit()
import sys
# Required for atexit.register()
import atexit
# Required for time.time()
import time
# Required for random number generation
import random
# Required for regular expressions
import re
# Required for the main command line argument parser
import argparse
# Required for os._exit()
import os


##########################################################################################
## Constants                                                                            ##
##########################################################################################


# Program exit codes (os.EX_OK, etc. are not cross-platform)
EXIT_SUCCESS = 0
EXIT_FAILURE_GENERAL = 1
EXIT_FAILURE_USAGE = 2

# Used for logging
LOG_LEVEL_DEBUG = 1
LOG_LEVEL_INFO = 2
LOG_LEVEL_WARN = 3
LOG_LEVEL_ERROR = 4
LOG_LEVEL_SYSTEM = 5
LOG_LEVEL_NONE = 100

# Used for database error tracking
DB_RESULT_OK = 0
DB_RESULT_GENERAL_FAILURE = 1
DB_RESULT_BAD_CHECKSUM = 2
DB_RESULT_CORRUPT_FILE = 3
DB_RESULT_NO_PERMISSION = 4
WARNING_DB_VALIDATION = 'Could not validate all database row checksums in {0}'
WARNING_DB_CORRUPTION = 'Significant corruption in {0} -- Attempting to write anyway'
ERROR_DB_PERMISSION = 'You do not have permission to access {0}'

# Used for keypress handling
KEY_SPACE = ' '
KEY_Q = 'Q'
KEY_X = 'X'
KEY_CTRL_C = '\x03'

# Standard log messages during the course of execution
APP_STARTUP_MSG = 'Application startup'
APP_SHUTDOWN_MSG = 'Application shutdown'
LOG_ENTRY_MSG = 'Daily Log entry written'
OS_DETECT_POSIX_MSG = 'Detected operating system: Linux/macOS'
OS_DETECT_NONPOSIX_MSG = 'Detected operating system: Windows'

# Used for identity indexing
ID_NAME = 0
ID_EMAIL = 1
ID_PHONE = 2

# Used for Operating System detection
OS_WINDOWS = 1
OS_NON_WINDOWS = 2

# SSOT for the web URL
WEB_URL = 'https://github.com/gregkrsak/phase-deuce'

# Used for the welcome banner
WELCOME_BANNER_LINE1 = 'Welcome to phase-deuce'
WELCOME_BANNER_LINE2 = 'Written by Greg M. Krsak (greg.krsak@gmail.com)'
WELCOME_BANNER_LINE3 = 'Contribute or file bugs here: {0}'.format(WEB_URL)
WELCOME_BANNER_LINE4 = 'Press SPACE to add a new log entry. Press Q or X or CTRL-C to exit.'

# Used for -h or --help arguments
ARG_HELP_DESCRIPTION =  'Welcome to the daily log. {0}'.format(WEB_URL)
# Used for -d or --date arguments
ARG_DATE_SHORT = '-d'
ARG_DATE_LONG = '--date'
ARG_DATE_DESCRIPTION = 'The desired logfile date in ISO 8601 format (YYYY-MM-DD)'

# Used for exception handling
EXCEPTION_GENERAL_MSG = 'Caught exception in {1}: {0}'
EXCEPTION_SYSTEMEXIT_MSG = 'Exiting early (probably because of command line options)'
EXCEPTION_DATE_INVALID_MSG = 'Date argument is invalid (Should be YYYY-MM-DD)'

# Have a problem? Use a regular expression. Now you have two problems!
# This regex validates an ISO 8601 date with the format YYYY-MM-DD
# Ref: https://stackoverflow.com/questions/22061723/regex-date-validation-for-yyyy-mm-dd
REGEX_ISO8601_DATEONLY = '^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$'
# This regex validates a 10-digit NANP telephone number with the format NPA-NXX-XXXX
# Ref: https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch04s02.html
REGEX_PHONE_US10DIGIT = '^\(?([2-9][0-8][0-9])\)?[-.]?([2-9][0-9]{2})[-.]?([0-9]{4})$'


##########################################################################################
## Functions                                                                            ##
##########################################################################################


def init(argv):
    """
    This is the code block that is run on startup.
    :return: Will exit with an EXIT_SUCCESS, EXIT_FAILURE_GENERAL, or EXIT_FAILURE_USAGE code.
    """
    app = Application()
    exit_code = app.run()
    sys.exit(exit_code)


def detect_os():
    """
    A rudamentary way to detect whether we are on Windows or a non-Windows operating system.
    :return: OS_WINDOWS or OS_NON_WINDOWS depending on the operating system.
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
    I am not the author of this function-- See the reference.
    Ref: https://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user
    :return: a Function object appropriate to the detected operating system.
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
    def __init__(self):
        self.buffer = ''

    def update(self):
        """
        Flush the output buffer.
        """
        pass


class Controller:
    """
    An abstract MVC controller.
    """
    def __init__(self):
        self.view = View()
        self.model = Model(self.view)


##########################################################################################
## Main program classes                                                                 ##
##########################################################################################


class Application(Controller):
    """
    The primary application code for the phase-deuce program.
    """

    def __init__(self):
        super().__init__()
        self.startup()

    def startup(self):
        """
        Performs tasks for the Application instance that should happen on startup.
        :return: None, or will exit with an EXIT_FAILURE_GENERAL, or EXIT_FAILURE_USAGE code.
        """
        # Initialize the internal logger (unrelated to writing to .CSV files)
        self.log = Log(LOG_LEVEL_INFO)

        result = True
        try:
            # Create the parser object for command line arguments
            parser = argparse.ArgumentParser(description=ARG_HELP_DESCRIPTION)
            # Define the -d or --date argument
            parser.add_argument(ARG_DATE_SHORT,
                                ARG_DATE_LONG,
                                help=ARG_DATE_DESCRIPTION,
                                required=False)
            # Execute the argument parser (this will cause a SystemExit exception on -h or --help)
            self.args = parser.parse_args()
            # Register the shutdown function
            atexit.register(self.shutdown)
            # Determine the proper (OS-specific) function to get keypresses
            self.getch = _find_getch()
            # Initialize the random number generator
            random.seed()
            # Initialize the primary MVC view to be an instance of the Log class
            self.view = self.log
            # Initialize the primary MVC model
            self.model = Database(self.view, self.args)
            # Validate the command line arguments
            self.validate_args()
        except SystemExit:
            # This exception is thrown by the argument parser
            result = False
            self.log.debug(EXCEPTION_SYSTEMEXIT_MSG)
            # Hard exit with a failure code. Note that this will bypass Application.shutdown()
            os._exit(EXIT_FAILURE_USAGE)
        except ValueError as e:
            # This exception is thrown by Application.validate_args()
            result = False
            self.log.error(str(e))
            # Exit with a failure code
            sys.exit(EXIT_FAILURE_USAGE)
        except:
            # Catch any other exception and do not raise
            result = False
            e = sys.exc_info()[0]
            self.log.error(EXCEPTION_GENERAL_MSG.format(e, 'Application.startup()'))
        finally:
            self.log.system(result, APP_STARTUP_MSG)

        if detect_os() == OS_WINDOWS:
            self.log.debug(OS_DETECT_NONPOSIX_MSG)
        else:
            self.log.debug(OS_DETECT_POSIX_MSG)
        return

    def run(self):
        """
        Runs the Application instance.
        :return: EXIT_SUCCESS
        """
        the_user_still_wants_to_run_this_application = True
        self.log.info(WELCOME_BANNER_LINE1)
        self.log.info(WELCOME_BANNER_LINE2)
        self.log.info(WELCOME_BANNER_LINE3)
        self.log.info(WELCOME_BANNER_LINE4)

        while the_user_still_wants_to_run_this_application:
            # Get a keypress from the user.
            if detect_os() == OS_NON_WINDOWS:
                user_input = self.getch()
            else:
                user_input = str(self.getch(), 'utf-8')
            # Did the user press SPACE?
            if user_input == KEY_SPACE:
                # Add a new row to the database
                db_result = DB_RESULT_OK
                write_succeeded = True
                db_result = self.model.create_row()
                # Only report a failed write if the Database object reports an unhandled exception
                # was thrown, or the user does not have the proper permissions. A checksum
                # validation failure will display a warning, but will probably not cause a failure
                # in the actual "append" mode write operation. The same goes for files with other
                # corruption issues (missing columns from one or more rows, etc.).
                if db_result == DB_RESULT_GENERAL_FAILURE or db_result == DB_RESULT_NO_PERMISSION:
                    write_succeeded = False
                self.log.system(write_succeeded, LOG_ENTRY_MSG)
            # Did the user press Q or X or CTRL-C?
            elif user_input.upper() == KEY_Q \
                or user_input.upper() == KEY_X \
                or user_input == KEY_CTRL_C:
                # Application will exit
                the_user_still_wants_to_run_this_application = False

        return EXIT_SUCCESS

    def shutdown(self):
        """
        Performs tasks for the Application instance that should happen on shutdown.
        :return: None
        """
        result = True
        try:
            pass # Do nothing
        except:
            # Was an exception thrown?
            result = False
        self.log.system(result, APP_SHUTDOWN_MSG)
        return

    def validate_args(self):
        """
        Validates the command line arguments. Raises an exception on failure.
        :return: None
        :raises: ValueError: A command line argument is invalid
        """
        # Check the -d parameter
        date_regex = re.compile(REGEX_ISO8601_DATEONLY)
        if self.args.date:
            if not date_regex.match(self.args.date):
                raise ValueError(EXCEPTION_DATE_INVALID_MSG)
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

    def __init__(self, log, command_line_args):
        super().__init__(log)
        self.command_line_args = command_line_args

    def todays_filename(self):
        """
        Calculates today's filename string using the ISO 8601 format date.
        :return: A string with the format "phase-deuce-log_YYYY-MM-DD.csv".
        """
        # Check to see if a date was provided in the command line arguments
        if not self.command_line_args.date:
            date_string = datetime.date.today().isoformat()
        else:
            date_string = self.command_line_args.date
        result = Database.filename_prefix + date_string + Database.filename_suffix
        return result

    def validate(self, filename=None):
        """
        Validates today's .CSV file.
        :return:
            DB_RESULT_OK
            DB_RESULT_GENERAL_FAILURE
            DB_RESULT_BAD_CHECKSUM
            DB_RESULT_CORRUPT_FILE
        """
        # Figure out the filaname
        if not filename:
            filename = self.todays_filename()
        # Default to success
        result = DB_RESULT_OK
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
                        result = DB_RESULT_BAD_CHECKSUM
                        break
            # Was there a checksum error?
            if result == DB_RESULT_BAD_CHECKSUM:
                self.view.warn(WARNING_DB_VALIDATION.format(filename))
        except IndexError as e:
            # This is caused by a corrupt database file. However, in many cases it should be
            # possible to append data to the file.
            result = DB_RESULT_CORRUPT_FILE
            self.view.warn(WARNING_DB_CORRUPTION.format(filename))
        except PermissionError:
            # User does not have permission to access the database file
            result = DB_RESULT_NO_PERMISSION
            self.view.error(ERROR_DB_PERMISSION.format(filename))
        except:
            # Was an exception thrown?
            result = DB_RESULT_GENERAL_FAILURE
            e = sys.exc_info()[0]
            self.view.error(EXCEPTION_GENERAL_MSG.format(e, 'Database.validate()'))

        return result


    def create_row(self):
        """
        Creates a database row that's populated with fake personally-identifying data.
        Note that the columns 'unix_time' and 'checksum' will be valid.
        :return:
            DB_RESULT_OK
            DB_RESULT_GENERAL_FAILURE
            DB_RESULT_BAD_CHECKSUM
            DB_RESULT_CORRUPT_FILE
        """
        filename = self.todays_filename()
        # Default to success
        result = DB_RESULT_OK
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
        except PermissionError:
            # User does not have permission to access the database file
            result = DB_RESULT_NO_PERMISSION
            self.view.error(ERROR_DB_PERMISSION.format(filename))
        except:
            # Was any other exception thrown?
            result = DB_RESULT_GENERAL_FAILURE
            e = sys.exc_info()[0]
            self.view.error(EXCEPTION_GENERAL_MSG.format(e, 'Database.create_row()'))
        return result


class Screen(View):
    """
    An MVC view representing the screen.
    """

    def __init__(self):
        super().__init__()

    def update(self):
        """
        Sends waiting buffer contents to the screen.
        :return: None
        """
        print(self.buffer)
        self.buffer = ''
        return


class Log(Screen):
    """
    This class logs application events to the screen.
    """

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
        """
        [OK] or [FAIL] messages.
        :return: None
        """
        if self.level <= LOG_LEVEL_SYSTEM:
            if status == True:
                self.__printlog(self.system_ok_string, message)
            else:
                self.__printlog(self.system_fail_string, message)
        return

    def debug(self, message):
        """
        [DEBUG] messages.
        :return: None
        """
        if self.level <= LOG_LEVEL_DEBUG:
            self.__printlog(self.debug_string, message)
        return

    def info(self, message):
        """
        [INFO] messages.
        :return: None
        """
        if self.level <= LOG_LEVEL_INFO:
            self.__printlog(self.info_string, message)
        return

    def warn(self, message):
        """
        [WARN] messages.
        :return: None
        """
        if self.level <= LOG_LEVEL_WARN:
            self.__printlog(self.warn_string, message)
        return

    def error(self, message):
        """
        [ERROR] messages.
        :return: None
        """
        if self.level <= LOG_LEVEL_ERROR:
            self.__printlog(self.error_string, message)
        return

    def __printlog(self, prefix_string, message):
        """
        Appends the appropriate log message to the MVC view's buffer, and triggers an update.
        :return: None
        """
        self.buffer += self.prefix_braces[0] + prefix_string + self.prefix_braces[1] \
                        + self.prefix_separator + message
        self.update()
        return


##########################################################################################
## Static Classes                                                                       ##
##########################################################################################


class PersonGenerator():
    """
    This is a static class used to generate pseudo-random "personal info".
    I was pretty tired when I wrote this, so forigve me if it looks like a giant hack.
    >> (Announcer's voice) 'It looks like a giant hack.' <<
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
        """
        Creates a new identity having a name, email address, and phone number.
        This is the public API interface for the PersonGenerator class.
        :return: a List object containing [0:name 1:email 2:phone]
        """
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
        """
        Generates a pseudo-random email address.
        :return: a String object containing an email address.
        """
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
        """
        Generates a pseudo-random NANP 10-digit phone number.
        :return: a String object containing a phone nunmber in the format NPA-NXX-XXXX.
        """
        nanp_regex = re.compile(REGEX_PHONE_US10DIGIT)
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
        """
        Attempts to generate a pseudo-random NANP NPA (NPA-NXX-XXXX).
        Note that the number returned by this function may not be valid according to the NANP.
        :return: an int between 0-999
        """
        result = random.randrange(0, 1000)
        return result

    def __generate_nxx():
        """
        Attempts to generate a pseudo-random NANP NXX (NPA-NXX-XXXX).
        Note that the number returned by this function may not be valid according to the NANP.
        :return: an int between 0-999
        """
        result = random.randrange(0, 1000)
        return result

    def __generate_xxxx():
        """
        Attempts to generate a pseudo-random NANP XXXX (NPA-NXX-XXXX).
        Note that the number returned by this function may not be valid according to the NANP.
        :return: an int between 0-9999
        """
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
