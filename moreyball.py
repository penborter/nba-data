import time
import pandas as pd
import numpy as np

from nba_api.stats.endpoints import leaguedashplayershotlocations

# Retry Wrapper 
def retry(func, retries=3):
    def retry_wrapper(*args, **kwargs):
        attempts = 0
        while attempts < retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(e)
                time.sleep(30)
                attempts += 1

    return retry_wrapper


def getShootingDF():
  
  @retry
  def getShootingData():
    data = leaguedashplayershotlocations.LeagueDashPlayerShotLocations()
    data = data.shot_locations.data

    # This section from nba_api package - couldn't get the built-in class method to work
    levels = []
    level_names = []
    for i in range(len(data["headers"])):  # Extend column names for level to full length
      level = data["headers"][i]
      level_names.append(
        level["name"] if "name" in level else "LEVEL_" + str(i)
      )
      column_names = (
        [""] * level["columnsToSkip"]
        if "columnsToSkip" in level
        else []
      )
      column_names += list(
        np.repeat(
          np.array(level["columnNames"]),
          level["columnSpan"] if "columnSpan" in level else 1,
        )
      )
      levels.append(column_names)
    midx = pd.MultiIndex.from_arrays(
      levels, names=level_names
    )  # Use MultiIndex for dataframe columns
    
    return pd.DataFrame(data["data"], columns=midx)


  shootingDF = getShootingData()
  for fg in ['FGM', 'FGA']:
    shootingDF.loc[:, ('Total Shots', fg)] = shootingDF.xs(fg, level=1, axis=1).sum(axis=1) - shootingDF['Corner 3'][fg]
    shootingDF.loc[:, ('Total from 3', fg)] = shootingDF[['Above the Break 3', 'Corner 3', 'Backcourt']].xs(fg, level=1, axis=1).sum(axis=1)
    shootingDF.loc[:, ('Pct RA', fg)] = round(shootingDF['Restricted Area'][fg] / shootingDF['Total Shots'][fg], 3)
    shootingDF.loc[:, ('Pct 3', fg)] = round(shootingDF['Total from 3'][fg] / shootingDF['Total Shots'][fg], 3)
    shootingDF.loc[:, ('Pct Moreyball', fg)] = round(shootingDF['Pct RA'][fg] + shootingDF['Pct 3'][fg], 3)

  shootingDF = shootingDF[shootingDF['Total Shots']['FGA'] > 200].sort_values(by=('Pct Moreyball', 'FGA'), ascending=False)
  shootingDF.columns = [col[1] if col[0] == "" else '_'.join(col) for col in shootingDF.columns.values]

  return shootingDF


shootingDF = getShootingDF()
shootingDF.to_csv('data/dynamic/Moreyball_Ranking.csv', index=False)