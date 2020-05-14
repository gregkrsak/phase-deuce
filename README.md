# phase-deuce

Welcome to the daily log.

# How do I use this?

phase-deuce is a console application, written in Python. That means you'll need to open a terminal window and execute it manually, from the command line.

If you don't have the Python language installed on your computer, you'll need to install it before this app will work.

# You said I need Python. How do I install Python?

###### Windows
- Go to [Python Downloads for Windows](https://www.python.org/downloads/windows/)
- Select and download *Windows x86-64 executable installer*
- Run the downloaded file
- This will bring up the Python wizard which will guide you throughout the installation
- Check the box __Add Python XX to PATH__, which will add Python to your Windows PATH; so you can run Python from anywhere inside your file system
- Accept all the default settings and wait until the installation is finished

###### Unix and Linux
- Open a web browser and head over to [Python Downloads](https://www.python.org/downloads/source/)
- Download the latest zipped source code available for Unix/Linux
- Download and extract files
- Open terminal and navigate to the directory where you extracted the files
- Run the following commands:
```bash
    ./configure
    make
    make install
```
- This will install Python at the default location `/usr/local/bin` and its libraries at `/usr/local/lib/pythonXX` where `XX` is the version of Python you installed
- Then set your `PATH` environment variable:

    In the bash shell, type `export PATH="$PATH:/usr/local/bin/python"` and press `ENTER`

    In the csh shell, type `setenv PATH "$PATH:/usr/local/bin/python"` and press `ENTER`

    In the sh or ksh shell, type `PATH="$PATH:/usr/local/bin/python"` and press `ENTER`

###### macOS
- Recent Macs come with Python pre-installed, but it might be outdated! Oh no!
- Checking the latest releases and related instructions might be a good idea, so [click here](https://www.python.org/downloads/mac-osx/)
- The macOS installer *should* automatically handle your path settings

# What does phase-deuce actually do?

Every time you press the space bar, a .CSV formatted row of data is added to a "daily log" database file. The database files are named according to the current day.

The rows of each daily log file are formatted with the following columns:

    unix_time,full_name,email_address,phone_number,checksum

Each log file will be named according to "phase-deuce-log_YYYY-MM-DD.csv"

# How do I use this again?

One you have the application running, just press `SPACE` every time you want to simulate a customer coming in.

When you're finished testing, press `Q`, `X`, or `CTRL-C` to exit.

To view the output data, open the .CSV file with Microsoft Excel, LibreOffice Calc, or any text editor.

(If you'd like to convert the UNIX timestamps to a friendlier datetime string, you can do a formula such as `=(A1/86400)+DATE(1970,1,1)` from within your spreadsheet, as shown [here](https://exceljet.net/formula/convert-unix-time-stamp-to-excel-date))

# Your code sucks. Can I make changes?

Yes! Please fork the repo and submit a pull request. I'd appreciate it.

Feel free to also submit a new issue if there's something you'd like me to address.
