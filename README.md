# OI-Downloader

Tool for downloading your solutions from [Szkopuł](https://szkopul.edu.pl/) for the [Polish Olympic in Informatics checklist](https://github.com/Matian37/oi-checklist).

It is required to provide **login** and **password** for tool to authenticate with the website.

## How It Works

Application runs headless browser and scrapes solutions from the [Szkopuł](https://szkopul.edu.pl/) website. 
After that it saves them in the checklist folder. 

To avoid making a huge number of requests, scores are retrieved from a single page (Szkopuł's OI Task Archive).
This means that:
* Solutions submitted to **separate contest** won't be **visible there**.
* Page shows result of your **latest submission**, **not the best one**.

Tool **does not download all solutions** from the website.
Solution is only downloaded when it has better score than the one already present in the checklist.
