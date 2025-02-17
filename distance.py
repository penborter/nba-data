import pandas as pd
import yaml
from nba_api.stats.endpoints import leaguedashptstats


def main():
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

  df = df[df.MIN > 500].sort_values(by='MILES_PER_36', ascending=False)

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

if __name__ == "__main__":
  main()