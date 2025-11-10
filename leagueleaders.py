import time
import pandas as pd
import yaml

from functools import wraps

from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.endpoints import leaguedashplayershotlocations
from nba_api.stats.endpoints import leaguedashptstats
from nba_api.stats.library.parameters import Season


from datetime import datetime
from utils.CourtPlot import CourtPlot
from utils.ShotDistance import get_shots_yml

# Retry Wrapper 
def retry(max_attempts=5, delay=5):
  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      attempts = 0
      print(f"Attempting {max_attempts} time(s).")
      while attempts < max_attempts:
        try:
          return func(*args, **kwargs)
        except Exception as e:
          print(f"Attempt {attempts + 1} failed: {e}")
          attempts += 1
          if attempts < max_attempts:
              print(f"Retrying in {delay} seconds...")
              time.sleep(delay)
      raise Exception(f"Function {func.__name__} failed after {max_attempts} attempts")
    return wrapper
  return decorator


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
  
# Implementing debugging for the shot locations API
from nba_api.stats.library.http import NBAStatsHTTP
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LoggedNBAStatsHTTP(NBAStatsHTTP):
    def send_api_request(self, endpoint, parameters, referer=None, proxy=None, headers=None, timeout=(20,120), raise_exception_on_error=False):
        logger.debug(f"Starting API request to {endpoint}")
        try:
            response = super().send_api_request(endpoint, parameters, referer, proxy, headers, timeout, raise_exception_on_error)
            logger.debug("Request completed successfully")
            logger.debug("Starting to process response")
            # Add any response info we can safely access
            return response
        except Exception as e:
            logger.error(f"Request failed with error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            raise

leaguedashplayershotlocations.NBAStatsHTTP = LoggedNBAStatsHTTP

@retry(max_attempts=2, delay=5)  
def get_shooting_data():
  """Fetch shooting data and process for Moreyball analysis."""

  shotLocations = leaguedashplayershotlocations.LeagueDashPlayerShotLocations(timeout=(20,30))  
  shotDF = shotLocations.shot_locations.get_data_frame()

  # Calculating Moreyball-specific stats from the shooting data, both makes and attempts
  for fg in ['FGM', 'FGA']:
    shotDF.loc[:, ('Total Shots', fg)] = shotDF.xs(fg, level=1, axis=1).sum(axis=1) - shotDF['Corner 3'][fg]
    shotDF.loc[:, ('Total from 3', fg)] = shotDF[['Above the Break 3', 'Corner 3', 'Backcourt']].xs(fg, level=1, axis=1).sum(axis=1)
    shotDF.loc[:, ('Pct RA', fg)] = round(shotDF['Restricted Area'][fg] / shotDF['Total Shots'][fg], 3)
    shotDF.loc[:, ('Pct 3', fg)] = round(shotDF['Total from 3'][fg] / shotDF['Total Shots'][fg], 3)
    shotDF.loc[:, ('Pct Moreyball', fg)] = round(shotDF['Pct RA'][fg] + shotDF['Pct 3'][fg], 3)
  
  # Sorting the df, min 50 FGA
  shotDF = shotDF[shotDF['Total Shots']['FGA'] > 50].sort_values(by=('Pct Moreyball', 'FGA'), ascending=False)
  shotDF.columns = [col[1] if col[0] == "" else '_'.join(col) for col in shotDF.columns.values]
  return shotDF

def save_to_csv(data, category, per_mode):
  """Save the data to a csv file"""

  if data is not None:
    csv_name = f'data/dynamic/NBA_Leaders_{category}_{per_mode}.csv'
    data.to_csv(csv_name,index=False)
    print(f"Data saved to {csv_name}")
  else:
    print(f"No data saved for {category} ({per_mode})")


def distance_leaders():
  # API request for player tracking stats
  df = leaguedashptstats.LeagueDashPtStats(
    per_mode_simple='Totals',
    player_or_team='Player',
    pt_measure_type='SpeedDistance'
  ).get_data_frames()[0]

  marathon_miles = 26.219

  # Updating the dataframe
  df['DIST_MARATHONS'] = df.DIST_MILES / marathon_miles
  df['MILES_PER_GAME'] = df.DIST_MILES / df.GP
  df['MILES_PER_36'] = df.DIST_MILES / df.MIN * 36

  df = df[df.MIN > 150].sort_values(by='MILES_PER_36', ascending=False)

  df.to_csv('data/dynamic/NBA_Leaders_Distance')
  distance_yaml_list = [{
    'id': str(df.iloc[i].PLAYER_ID),
    'name': str(df.iloc[i].PLAYER_NAME),
    'team': str(df.iloc[i].TEAM_ABBREVIATION),
    'games': str(df.iloc[i].GP),
    'minutes': str(df.iloc[i].MIN),
    'miles': str(df.iloc[i].DIST_MILES),
    'avg_speed': str(df.iloc[i].AVG_SPEED),
    'marathons': str(df.iloc[i].DIST_MARATHONS),
    'miles_per_game': str(df.iloc[i].MILES_PER_GAME),
    'miles_per_thirty': str(df.iloc[i].MILES_PER_36)}
    for i in range(len(df) - 1)]

  with open('distance.yml', 'w') as stream:
    yaml.dump(distance_yaml_list, stream)


def main():
  # Request and save data
  categories = ['MOREYBALL', 'PTS', 'REB', 'AST'] # Taking out the Moreyball category until I figure out what's causing the timeout
  for category in categories:
    if category == 'PTS':
      for mode in ['PerGame', 'Totals']:
        data = get_league_leaders(category, mode)
        save_to_csv(data, category, mode)
    elif category == 'MOREYBALL':
      try:
        data = get_shooting_data()
        mb_leader_name = data.iloc[0,1]
        save_to_csv(data, category, 'Rate')

        # Save .yml file for Moreyball data
        mb_full_yaml_list =  [{
          'id': str(data.iloc[i].PLAYER_ID),
          'name': str(data.iloc[i].PLAYER_NAME),
          'team': str(data.iloc[i].TEAM_ABBREVIATION),
          'RA_FGM': str(data.iloc[i]['Restricted Area_FGM']),
          'RA_FGA': str(data.iloc[i]['Restricted Area_FGA']),
          'RA_PCT': str(data.iloc[i]['Pct RA_FGA']),
          'THREE_FGM': str(data.iloc[i]['Total from 3_FGM']),
          'THREE_FGA': str(data.iloc[i]['Total from 3_FGA']),
          'THREE_PCT': str(data.iloc[i]['Pct 3_FGA']),
          'MB_FGM': str(data.iloc[i]['Total from 3_FGM'] + data.iloc[i]['Restricted Area_FGM']),
          'MB_FGA': str(data.iloc[i]['Total from 3_FGA'] + data.iloc[i]['Restricted Area_FGA']),
          'TOTAL_FGM': str(data.iloc[i]['Total Shots_FGM']),
          'TOTAL_FGA': str(data.iloc[i]['Total Shots_FGA']),
          'MB_PCT': str(data.iloc[i]['Pct Moreyball_FGA'])} 
          for i in range((len(data) - 1))]

        with open('moreyball_full.yml', 'w') as stream:
          yaml.dump(mb_full_yaml_list, stream)

      except  Exception as e:
        print(f"Moreyball data not saved: {e}")
    else:
      data = get_league_leaders(category, 'PerGame')
      save_to_csv(data, category, 'PerGame')

  # Plot Moreyball leader
  mbPlot = CourtPlot(mb_leader_name, bg="#e4dbcd", ec="#403126", fc="#efd5b9")
  mbPlot.plot_shots(title_text="Moreyball Pct. League Leader",
                    subtitle_text=mbPlot.player_name + " (as of {date}, min. 100 FGA)".format(date=datetime.today().strftime('%Y-%m-%d')),
                    save_plot=True)
  
  # Get distance leaders data
  distance_leaders()

  # Get shooting distance data
  get_shots_yml()


if __name__ == "__main__":
  main()