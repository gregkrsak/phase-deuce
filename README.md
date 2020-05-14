# phase-deuce

Welcome to the daily log.

# How do I use this?

phase-deuce is a console application. That means you'll need to open a terminal window and execute it manually, from the command line. You'll need to install Python first.

# How do I install Python?

###### Unix and Linux
- Open a web browser and head over to [Python Downloads](https://www.python.org/downloads/source/)
- Download the latest zipped source code available for Unix/Linux
- Download and extract files
- Open terminal and navigate to the directory where you extracted the files
- Run the following commands:

    __./configure__

    __make__

    __make install__
- This will install Python at the default location */usr/local/bin* and its libraries at */usr/local/lib/pythonXX* where *XX* is the version of Python you installed
- To Set Path:

    In the csh shell − type __setenv PATH "$PATH:/usr/local/bin/python"__ and press enter

    In the bash shell (Linux) − type __export PATH="$PATH:/usr/local/bin/python"__ and press enter

    In the sh or ksh shell − type __PATH="$PATH:/usr/local/bin/python"__ and press enter

###### Mac OS
- Recent Macs come with Python pre-installed, but it might be outdated
- For checking on latest releases and related instructions, [click here](https://www.python.org/downloads/mac-osx/)
- In case you're using a version before Mac OS X 10.3 (released in 2003), MacPython is available
- Jack Jensen maintains it and you can take a look at his full docs on his website [over here](https://homepages.cwi.nl/~jack/macpython/index.html)
- Mac installer automatically handles path, so the users don't have to set it manually

###### Windows
- Go to [Python Downloads for Windows](https://www.python.org/downloads/windows/)
- Select and download *Windows x86-64 executable installer*
- Run the downloaded file
- This will bring up the Python wizard which will guide you throughout the installation
- Check the box __Add Python XX to PATH__, which will add Python to your Windows PATH; so you can run Python from anywhere inside your file system
- Accept all the default settings and wait until the installation is finished

# What does phase-deuce actually do?

Every time you press the space bar, a .CSV formatted row of data is added to a "daily log" database file. The database files are named according to the current day.

The columns of each daily log file are formatted as follows:

    unix_time,full_name,email_address,phone_number,checksum

Each log file will be named according to "phase-deuce-log_YYYY-MM-DD.csv"

# How do I use this again?

One you have the application running, just press `SPACE` every time you want to simulate a customer coming in.

When you're finished testing, press `Q` or `X` to exit.

To view the output data, open the .CSV file with Microsoft Excel, LibreOffice Calc, or any text editor.

# Your code sucks. Can I make changes?

Yes! Please fork the repo and submit a pull request. I'd appreciate it.

Feel free to also submit a new issue if there's something you'd like me to address.
