import pandas as pd

from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.library.parameters import Season


def get_data(cat, per_mode):

  try:
    leagueLead = leagueleaders.LeagueLeaders(league_id='00',
                                          per_mode48=per_mode,
                                          scope='S',
                                          season=Season.default,
                                          season_type_all_star='Regular Season',
                                          stat_category_abbreviation=cat)
    
    # Export just the top 30 to csv
    leaders = leagueLead.league_leaders.get_data_frame()
    csv_name = 'data/dynamic/NBA_Leaders_' + cat + per_mode + '.csv'
    leaders.iloc[:30].to_csv(csv_name,index=False)
  except:
    return


# Extract and export the info for each of the listed categories
categories = ['PTS', 'REB', 'AST']

for cat in categories:
  if cat == 'PTS':
    get_data(cat, 'PerGame')
    get_data(cat, 'Totals')
  else:
    per_mode = 'PerGame'
    get_data(cat, per_mode)