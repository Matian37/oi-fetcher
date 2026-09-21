# OI-Downloader

Tool for downloading your solutions from [Szkopuł](https://szkopul.edu.pl/) for the [Polish Olympic in Informatics checklist](https://github.com/Matian37/oi-checklist).

## How It Works

Application runs headless browser and scrapes solutions from the [Szkopuł](https://szkopul.edu.pl/) website. After that it saves them in the checklist folder. To download solutions it is required to provide **login** and **password**.

To avoid making a huge number of requests to the website, scores are retrieved from single page (OI Task Archive).

* Keep in mind that if you submitted a solution to a **separate contest**, it will be **not visible** here.
* Additionally, this page shows the result of your **latest submission**, **not best one**.

Tool **does not download all solutions** from the website. Solution is only downloaded when it has better score than the one already present in the checklist.
