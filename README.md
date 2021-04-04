# Zillow Scraper


This repo allows the user to scrape Zillow for properties in Chicago meeting certain criteria\*.
It's divided into two parts: a scraper and a processing pipeline.

The **scraper** pulls all properties added to Zillow within the last week that meet the criteria and stores them as a JSON file in `raw_data/`, named by date.
For example, data pulled on Jan 13, 2021 would be stored in `raw_data/20210113.json`.
The scraper is invoked as follows:
```bash
python -m zillow-scraper.scrape [max-pages]
```
The `max-pages` argument is optional, and indicates how many search pages to search through before stopping.
If omitted, the scraper will exhaust all pages.
(Providing `max-pages` is mainly useful for testing.)

The **pipeline** hasn't been built yet.


\* The city and criteria could be modified but are not parameterized.
