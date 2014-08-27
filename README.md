WCA-forum-statistics-tool
=========================

Produces statistics from WCA data for speedsolving.com forum posts. Automatically updates a local database using the WCA export. Not an official WCA tool.

You write queries in `*.in` textfiles and the tool runs them and produces `*.out` textfiles that contain the results nicely formatted and documented, ready to copy&paste into the forum. The three examples in this repository were posted here: [Female Podiums](http://www.speedsolving.com/forum/showthread.php?26121-Odd-WCA-stats-Stats-request-Thread&p=1011290&viewfull=1#post1011290), [Average 3x3 time by year](http://www.speedsolving.com/forum/showthread.php?26121-Odd-WCA-stats-Stats-request-Thread&p=1008461&viewfull=1#post1008461), [FMC statistics per year](http://www.speedsolving.com/forum/showthread.php?48994-Proposal-allow-a-move-limit-for-FMC&p=1009075&viewfull=1#post1009075).

What you need and where to get it (if you don't have it already):
- [Python 3](https://www.python.org/downloads/) (to run the tool)
- [MySQL Community Server](http://dev.mysql.com/downloads/) (to hold the WCA export data)
- A database and user, see the settings section at the start of the tool.
- [MySQL Connector/Python](http://dev.mysql.com/downloads/connector/python/) (so Python can access the database)

There's a [speedsolving.com thread](http://www.speedsolving.com/forum/showthread.php?49120) about it.
