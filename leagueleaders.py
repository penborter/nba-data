import pandas as pd

from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.library.parameters import Season


def get_league_leaders(category, per_mode, top_n=50):
  """Fetch league leaders data for a given category and mode."""

  try:
    leagueLead = leagueleaders.LeagueLeaders(league_id='00',
                                          per_mode48=per_mode,
                                          scope='S',
                                          season=Season.default,
                                          season_type_all_star='Regular Season',
                                          stat_category_abbreviation=category
    ).league_leaders.get_data_frame()    
    return leagueLead.head(top_n)
  
  except Exception as err:
    print(f"Error fetching data for {category} ({per_mode}): {err}")
    return None

def save_to_csv(data, category, per_mode):
  """Save the data to a csv file"""

  if data is not None:
    csv_name = f'data/dynamic/NBA_Leaders_{category}_{per_mode}.csv'
    data.to_csv(csv_name,index=False)
    print(f"Data saved to {csv_name}")
  else:
    print(f"No data to save for {category} ({per_mode})")

def main():

  categories = ['PTS', 'REB', 'AST']
  for category in categories:
    if category == 'PTS':
      for mode in ['PerGame', 'Totals']:
        data = get_league_leaders(category, mode)
        save_to_csv(data, category, mode)
    else:
      data = get_league_leaders(category, 'PerGame')
      save_to_csv(data, category, 'PerGame')

if __name__ == "__main__":
  main()