import pandas as pd
from nba_api.stats.endpoints import leaguedashplayershotlocations

def get_shooting_data():
  data = leaguedashplayershotlocations.LeagueDashPlayerShotLocations()
  return data.shot_locations.get_data_frame()

def process_shooting_data(shootingDF):
  for fg in ['FGM', 'FGA']:
    shootingDF.loc[:, ('Total Shots', fg)] = shootingDF.xs(fg, level=1, axis=1).sum(axis=1) - shootingDF['Corner 3'][fg]
    shootingDF.loc[:, ('Total from 3', fg)] = shootingDF[['Above the Break 3', 'Corner 3', 'Backcourt']].xs(fg, level=1, axis=1).sum(axis=1)
    shootingDF.loc[:, ('Pct RA', fg)] = round(shootingDF['Restricted Area'][fg] / shootingDF['Total Shots'][fg], 3)
    shootingDF.loc[:, ('Pct 3', fg)] = round(shootingDF['Total from 3'][fg] / shootingDF['Total Shots'][fg], 3)
    shootingDF.loc[:, ('Pct Moreyball', fg)] = round(shootingDF['Pct RA'][fg] + shootingDF['Pct 3'][fg], 3)

  shootingDF = shootingDF.sort_values(by=('Pct Moreyball', 'FGA'), ascending=False)
  shootingDF.columns = [col[1] if col[0] == "" else '_'.join(col) for col in shootingDF.columns.values]

  return shootingDF

def save_to_csv(df, filename="data/dynamic/Moreyball_Ranking.csv"):
  df.to_csv(filename, index=False)


def main():
  try:
    shooting_df = get_shooting_data()
    processed_df = process_shooting_data(shooting_df)
    save_to_csv(processed_df)
  except Exception as e:
    print(f"An error occurred: {e}")


if __name__ == "__main__":
  main()