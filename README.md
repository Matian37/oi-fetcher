# OI-Downloader

Tool for downloading your solutions from [Szkopuł](https://szkopul.edu.pl/) for the [Polish Olympic in Informatics checklist](https://github.com/Matian37/oi-checklist).

It is required to provide **login** and **password** for tool to authenticate with the website.

## Installation

Download the latest binary from [Releases](https://github.com/Matian37/oi-downloader/releases) for your OS and architecture.

## How It Works

Application scrapes solutions from the [Szkopuł](https://szkopul.edu.pl/) website. 
After that it saves them in the checklist folder. 

To avoid making a huge number of requests, scores are retrieved from a single page (Szkopuł's OI Task Archive).
This means that:
* Solutions submitted to **separate contest** won't be **visible there**.
* Page shows result of your **latest submission**, **not the best one**.

Tool **does not download all solutions** from the website.
Solution is only downloaded when it has better score than the one already present in the checklist.

## Migrations

If you used the tool before version `0.2.0`, you should rebuild your checklist. Keep in mind that your older solutions will be removed, only the latest one will be kept. 

To rebuild checklist, remove the old checklist folder, then run updated tool again.

## Development

To run the tool from source you need [uv](https://docs.astral.sh/uv/) (Python 3.13+):

```bash
git clone https://github.com/Matian37/oi-downloader
cd oi-downloader
uv run oi-downloader
```

To run the tests, use `uv run pytest`.
