# NBA Data Tools and Utilites

[![Weekly League Leaders](https://github.com/penborter/nba-data/actions/workflows/actions.yml/badge.svg)](https://github.com/penborter/nba-data/actions/workflows/actions.yml)

Collecting existing data and tools I've put together for analysing NBA data.
Will continue to add to the collection as I clean things up.

Relies heavily on the [nba_api](https://github.com/swar/nba_api) Python package.

## NBA.ben.report

The League Leaders action tracked above links to leaderboards on [NBA.ben.report](https://nba.ben.report).

## Data

Using Github Actions to scrape the daily League Leaders for points, rebounds and assists (for now). 


Based on [git scraping](https://simonwillison.net/2020/Oct/9/git-scraping/), as described by Simon Willison.
The changelog of the csv files can be used to show how the league leaders have changed over the course of the season.

## Utilities

Cleaning up and collecting an assortment of analysis utilties, mostly jupyter notebooks.
Currently available:

- [Advanced Video Stats](https://github.com/penborter/nba-data/blob/main/utilities/Advanced%20Stats%20Video.ipynb): Tool to get the video URL for any NBA play based on the `GAME_ID` and `EVENTNUM`
- [PBP Possessions](https://github.com/penborter/nba-data/blob/main/utilities/PBP%20Possessions.ipynb): Tool to expand on NBA-provided play-by-play data, adding info for possession analysis of a game. 
