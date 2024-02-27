import numpy as np
import pandas as pd

from nba_api.stats.endpoints import leaguedashplayershotlocations


## Extracted from nba_api - for some reason doesn't work as in-built class method
def get_data_frame(data):

    if isinstance(data["headers"][0], str):
        return DataFrame(data["data"], columns=data["headers"])

    else:  # Multiple levels of column names
        levels = []
        level_names = []
        for i in range(
            len(data["headers"])
        ):  # Extend column names for level to full length
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
    

try:
  playerShotlocs = leaguedashplayershotlocations.LeagueDashPlayerShotLocations()
  playershotsDF = get_data_frame(playerShotlocs.shot_locations.data)

except Exception as err:
    print(f'Error: {err}')

finally:
  # Add new columns to calculate Moreyball percentage
  for fg in ['FGM', 'FGA']:
      playershotsDF.loc[:, ('Total Shots', fg)] = playershotsDF.xs(fg, level=1, axis=1).sum(axis=1) - playershotsDF['Corner 3'][fg]
      playershotsDF.loc[:, ('Total from 3', fg)] = playershotsDF[['Above the Break 3', 'Corner 3', 'Backcourt']].xs(fg, level=1, axis=1).sum(axis=1)
      playershotsDF.loc[:, ('Pct RA', fg)] = round(playershotsDF['Restricted Area'][fg] / playershotsDF['Total Shots'][fg], 3)
      playershotsDF.loc[:, ('Pct 3', fg)] = round(playershotsDF['Total from 3'][fg] / playershotsDF['Total Shots'][fg], 3)
      playershotsDF.loc[:, ('Pct Moreyball', fg)] = round(playershotsDF['Pct RA'][fg] + playershotsDF['Pct 3'][fg], 3)


  sortedDF = playershotsDF[playershotsDF['Total Shots']['FGA'] > 200].sort_values(by=('Pct Moreyball', 'FGA'), ascending=False)
  sortedDF.columns = [col[1] if col[0] == "" else '_'.join(col) for col in sortedDF.columns.values]

  sortedDF.to_csv('data/dynamic/Moreyball_Ranking.csv', index=False)