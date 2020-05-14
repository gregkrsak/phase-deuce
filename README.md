# phase-deuce

Welcome to the daily log.

# How do I use this?

phase-deuce is a console application. That means you'll need to open a terminal window and execute it manually, from the command line.

# What does it actually do?

Every time you press the space bar, a .CSV formatted row of data is added to a "daily log" database file. The database files are named according to the current day.

The columns of each daily log file are formatted as follows:

    unix_time,full_name,email_address,phone_number,checksum

Each log file will be named according to "phase-deuce-log_YYYY-MM-DD.csv"

# How do I use this again?

One you have the application running, just press `SPACE` every time you want to simulate a customer coming in.

When you're finished testing, press `Q` or `X` to exit.

To view the output data, open the .CSV file with Microsoft Excel, LibreOffice Calc, or any text editor.
