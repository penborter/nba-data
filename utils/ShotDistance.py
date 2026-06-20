import pandas as pd
import numpy as np
import yaml
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.static import teams

# Helper function for number formatting
def fmt(val):
  return round(val, 3) if pd.notnull(val) else ""

def _season_string_from_end_date(end_date_str):
  """Convert NBA_SEASON_END (YYYY-MM-DD) to nba_api season string e.g. '2025-26'."""
  year = int(end_date_str[:4])
  # The end date falls in the latter year of the season label (e.g. 2026 → 2025-26)
  return f"{year - 1}-{str(year)[2:]}"

def get_shots_yml():
  """
  Using shot chart data from NBA_API, aggregate and re-format data to return shooting distance data.
  For all players, for current season up to date of request.
  Saves result to yaml file called 'shot_distance.yml'
  """

  # Derive season from env var so post-season API calls still target the right year
  season_end = os.environ.get('NBA_SEASON_END')
  season = _season_string_from_end_date(season_end) if season_end else None

  kwargs = dict(team_id=0, player_id=0, context_measure_simple='FGA')
  if season:
    kwargs['season_nullable'] = season

  # NBA API requests
  shotdf = shotchartdetail.ShotChartDetail(**kwargs).get_data_frames()[0]
  teams_list = teams.get_teams()

  shotdf['POINT_VALUE'] = np.where(shotdf['SHOT_ZONE_BASIC'].str.contains('3'), '3', '2')

  # Create aggregated dataframe for average distances
  # Masks
  is_three = shotdf['POINT_VALUE'] == '3'
  is_two = shotdf['POINT_VALUE'] == '2'
  made = shotdf['SHOT_MADE_FLAG'] == 1
  missed = shotdf['SHOT_MADE_FLAG'] == 0

  # Helper for agg
  def agg_dist(df):
      return df.groupby('PLAYER_ID').agg(
          FGA=('SHOT_DISTANCE', 'count'),
          ALL_AVG_DISTANCE=('SHOT_DISTANCE', 'mean'),
          _3PT_AVG_DISTANCE=('SHOT_DISTANCE', lambda x: x[is_three.loc[x.index]].mean()),
          _2PT_AVG_DISTANCE=('SHOT_DISTANCE', lambda x: x[is_two.loc[x.index]].mean())
      ).rename(columns={
          '_3PT_AVG_DISTANCE': '3PT_AVG_DISTANCE',
          '_2PT_AVG_DISTANCE': '2PT_AVG_DISTANCE'
      })

  # Full stats
  all_df = agg_dist(shotdf).add_prefix('ALL_')
  made_df = agg_dist(shotdf[made]).add_prefix('MADE_')
  miss_df = agg_dist(shotdf[missed]).add_prefix('MISS_')

  # Combine into one df
  out = (
      all_df.join(made_df, how='outer')
            .join(miss_df, how='outer')
            .reset_index()
  )

  # Add player names and teams
  names = shotdf[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID']].drop_duplicates(subset=['PLAYER_ID'])
  out = out.merge(names, on='PLAYER_ID', how='left')
  out['TEAM_ABBREVIATION'] = out['TEAM_ID'].map({team['id']: team['abbreviation'] for team in teams_list})

  # Filter and re-order
  out = out[out.ALL_FGA > 50].sort_values('ALL_ALL_AVG_DISTANCE', ascending=False)

  if out.empty:
    print("Shot distance data is empty — skipping file writes to preserve existing data.")
    return

  out.to_csv('SHOOTING_DISTANCE_24-25.csv')

  shot_distance_list = [{
      'id': str(row.PLAYER_ID),
      'name': str(row.PLAYER_NAME),
      'team': str(row.TEAM_ABBREVIATION),
      'fga': str(row.ALL_FGA),
      'all_avg_dist': fmt(row.ALL_ALL_AVG_DISTANCE),
      'thr_avg_dist': fmt(row.ALL_3PT_AVG_DISTANCE),
      'two_avg_dist': fmt(row.ALL_2PT_AVG_DISTANCE),
      'made_fga': str(row.MADE_FGA),
      'made_all_avg_dist': fmt(row.MADE_ALL_AVG_DISTANCE),
      'made_thr_avg_dist': fmt(row.MADE_3PT_AVG_DISTANCE),
      'made_two_avg_dist': fmt(row.MADE_2PT_AVG_DISTANCE),
      'miss_fga': str(row.MISS_FGA),
      'miss_all_avg_dist': fmt(row.MISS_ALL_AVG_DISTANCE),
      'miss_thr_avg_dist': fmt(row.MISS_3PT_AVG_DISTANCE),
      'miss_two_avg_dist': fmt(row.MISS_2PT_AVG_DISTANCE),
  } for _, row in out.iterrows()]


  with open('shot_distance.yml', 'w') as stream:
    yaml.dump(shot_distance_list, stream)