import pandas as pd

from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.endpoints import leaguedashplayershotlocations
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
  
def get_shooting_data():
  """Fetch shooting data and process for Moreyball analysis."""

  try:
    shotLocations = leaguedashplayershotlocations.LeagueDashPlayerShotLocations()
    shotDF = shotLocations.shot_locations.get_data_frame()

    # Calculating Moreyball-specific stats from the shooting data, both makes and attempts
    for fg in ['FGM', 'FGA']:
      shotDF.loc[:, ('Total Shots', fg)] = shotDF.xs(fg, level=1, axis=1).sum(axis=1) - shotDF['Corner 3'][fg]
      shotDF.loc[:, ('Total from 3', fg)] = shotDF[['Above the Break 3', 'Corner 3', 'Backcourt']].xs(fg, level=1, axis=1).sum(axis=1)
      shotDF.loc[:, ('Pct RA', fg)] = round(shotDF['Restricted Area'][fg] / shotDF['Total Shots'][fg], 3)
      shotDF.loc[:, ('Pct 3', fg)] = round(shotDF['Total from 3'][fg] / shotDF['Total Shots'][fg], 3)
      shotDF.loc[:, ('Pct Moreyball', fg)] = round(shotDF['Pct RA'][fg] + shotDF['Pct 3'][fg], 3)
    
    # Sorting the df, also filter by min shots later in the season
    shotDF = shotDF.sort_values(by=('Pct Moreyball', 'FGA'), ascending=False)
    shotDF.columns = [col[1] if col[0] == "" else '_'.join(col) for col in shotDF.columns.values]
    return shotDF
  
  except Exception as err:
    print(f"Error fetching data for shot locations: {err}")
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

  categories = ['PTS', 'MOREYBALL' 'REB', 'AST']
  for category in categories:
    if category == 'PTS':
      for mode in ['PerGame', 'Totals']:
        data = get_league_leaders(category, mode)
        save_to_csv(data, category, mode)
    elif category == 'MOREYBALL':
      data = get_shooting_data()
      save_to_csv(data, category, 'Rate')
    else:
      data = get_league_leaders(category, 'PerGame')
      save_to_csv(data, category, 'PerGame')

if __name__ == "__main__":
  main()