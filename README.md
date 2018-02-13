# NCSA-Request-log-analyzer

A basic python script that analyzes the request log created from your web server, which is in NCSA format.

It assumes the log directory is `/var/log/oms/` and log file names are of the format `access-2018_02_12.log`.

It provides :
* Total number of APIs hit in a day
* API hits per hour
* Most frequent APIs
* Top 20 slowest APIs

The script is tested with the log file generated with the below Java code in Spring boot with Jetty :
~~~
NCSARequestLog reqLogImpl = new NCSARequestLog("/var/log/oms/access-yyyy_mm_dd.log");
reqLogImpl.setRetainDays(30);
reqLogImpl.setAppend(true);
reqLogImpl.setExtended(false);
reqLogImpl.setLogTimeZone("IST");
reqLogImpl.setLogLatency(true);
~~~
