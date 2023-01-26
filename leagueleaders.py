import pandas as pd

from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.library.parameters import Season

# Current league leaders in PTS per game
leagueLead = leagueleaders.LeagueLeaders(league_id='00',
                                         per_mode48='PerGame',
                                         scope='S',
                                         season=Season.default,
                                         season_type_all_star='Regular Season',
                                         stat_category_abbreviation='PTS')

# Export just the top 30 to csv
leaders = leagueLead.get_data_frame()
leaders.iloc[:30].to_csv('league_leaders.csv',index=False)
