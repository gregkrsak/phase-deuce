# phase-deuce

Welcome to the daily log. This program was written during the COVID-19 pandemic, as a way to demonstrate that manual "contact tracing" can be spoofed.

The code is cross-platform, and most of it is (I think) written well. Let me know what you think.

# How do I use this?

###### Windows
From the command line, type `phase-deuce.py` (or `phase-deuce.py -h` for a list of options)

###### macOS/Linux
From the command line, type `./phase-deuce.py` (or `./phase-deuce.py -h` for a list of options)

Note that phase-deuce is a console application, written in Python. That means you'll need to open a terminal window and execute it manually, from the command line. *If you don't already have the Python language installed on your computer, you'll need to install it before this app will work.*

# What does phase-deuce actually do?

Every time you press the space bar, a .CSV formatted row of data is added to a "daily log" database file. The database files are named according to the current day.

The rows of each daily log file are formatted with the following columns:

    unix_time,full_name,email_address,phone_number,checksum

Each log file will be named according to "phase-deuce-log_YYYY-MM-DD.csv"

# I'm not sure if I can run Python apps. How do I install Python?

###### Windows
- First of all, try to install Python from the Windows Store. If you're unable to do this, keep reading...
- Go to [Python Releases for Windows](https://www.python.org/downloads/windows/)
- Under *Stable Releases*, select and download the most recent *Windows x86-64 executable installer*
- Run the downloaded file
- This will bring up the Python wizard which will guide you throughout the installation
- Choose *Customize installation*
- Check the box *Add Python to environment variables*, so you can run Python from any folder
- Accept the remaining settings and wait until the installation is finished

###### macOS
- Recent Macs come with Python pre-installed, but it *might* be outdated! (Oh no!)
- Checking the latest releases and related instructions might be a good idea, so [click here](https://www.python.org/downloads/mac-osx/)
- The macOS installer *should* automatically handle your path settings

###### Unix and Linux
- First of all, try to install Python using your package manager. If you're unable to do this, keep reading...
- Open a web browser and head over to [Python Source Releases](https://www.python.org/downloads/source/)
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

# How do I use this again?

One you have the application running, just press `SPACE` every time you want to simulate a customer coming in.

When you're finished testing, press `Q`, `X`, or `CTRL-C` to exit.

To view the output data, open the .CSV file with Microsoft Excel, LibreOffice Calc, or any text editor.

(If you'd like to convert the UNIX timestamps to a friendlier datetime string, you can do a formula from within your spreadsheet, as shown [here](https://exceljet.net/formula/convert-unix-time-stamp-to-excel-date))

# Your code sucks. Can I make changes?

Yes! Please fork the repo and submit a pull request. I'd appreciate it.

Feel free to also submit a new issue if there's something you'd like me to address.
