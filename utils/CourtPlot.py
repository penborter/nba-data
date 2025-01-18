
import time
import pandas as pd
import numpy as np
import requests

from functools import wraps
from io import BytesIO
from PIL import Image

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Circle, Rectangle, Arc, Wedge
from pathlib import Path

from nba_api.stats.static import players
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.library.parameters import Season

# Setting Inter SemiBold as custom font
font_path = Path(__file__).parent / "fonts/DepartureMono-Regular.otf"
fm.fontManager.addfont(str(font_path))
custom_font = fm.FontProperties(fname=str(font_path)).get_name()

class CourtPlot:
    def __init__(self, player_name, season=Season.current_season, bg='#F4F5EF', ec='#2A4644', fc='#FBE9E2', percent=100):
        # Initialize attributes for player and court settings
        self.player_name = player_name
        self.season = season
        self.bg = bg
        self.ec = ec
        self.fc = fc
        self.percent = percent
        self.player_id = self._get_player_id(player_name)
        self.shots_df = self._fetch_shot_data()
        self.player_pic = self._fetch_player_pic()

    def _get_player_id(self, player_name):
        # Fetch player ID based on name
        player_dict = players.get_active_players()
        return next((player['id'] for player in player_dict if player['full_name'].lower() == player_name.lower()), None)

    def _fetch_shot_data(self):
        try:
            return shotchartdetail.ShotChartDetail(
                team_id=0,
                player_id=self.player_id,
                season_nullable=self.season,
                context_measure_simple='FGA'
            ).shot_chart_detail.get_data_frame()
        except Exception as e:
            print(f"Failed to fetch shot data: {e}")
            return pd.DataFrame()  # Return empty DataFrame on failure
        
    def _fetch_player_pic(self):
        url_address = f'https://cdn.nba.com/headshots/nba/latest/1040x760/{self.player_id}.png'
        response = requests.get(url_address) # Send http request to the url address
      
        # Make sure everything went right
        if response.status_code == 200:
            image_bytes = BytesIO(response.content) # Get content 
            image = Image.open(image_bytes) # Open the image
            return image # Output
        else:
            print("Failed to download image:", response.status_code)

    def draw_court(self, ax=None, halfcourt=True, moreyball=False):
        # Draw the court elements on a matplotlib axis
        if ax is None:
            ax = plt.gca()
        
        # Apply color settings and create court patches
        fc = self.fc if moreyball else self.bg
        court_elements = [
            Wedge((0, 0), 238.5, theta1=22.25, theta2=157.75, lw=0, fc=fc),         # 3pt arc shading
            Rectangle((-220.5, -47.5), 441, 137.5, lw=0, fc=fc),                    # 3pt rectangle shading
            Rectangle((-80, -47.5), 160, 190, lw=1.5, ec=self.ec, fc=fc),           # Key lines
            Arc((0, 142.5), 120, 120, theta1=0, theta2=180, lw=1.5, ec=self.ec),    # Free throw top arc 
            Arc((0, 142.5), 120, 120, theta1=180, theta2=0, lw=1.5, ec=self.ec),    # Free throw bottom arc
            Arc((0, 0), 477, 477, theta1=22.25, theta2=157.75, lw=1.5, ec=self.ec), # Three-point arc
            Rectangle((-220.5, -47.5), 0, 137.5, lw=1.5, ec=self.ec),               # Three-point right corner
            Rectangle((220.5, -47.5), 0, 137.5, lw=1.5, ec=self.ec),                # Three-point left corner
            Circle((0, 0), radius=40, lw=0, fc=self.bg),                            # Restricted area shading
            Arc((0, 0), 80, 80, theta1=0, theta2=180, lw=1.5, ec=self.ec),          # Restricted area line
            Circle((0, 0), radius=7.5, lw=1.5, ec=self.ec, fill=False),             # Hoop
            Rectangle((-30, -11), 60, 0, lw=1.5, ec=self.ec),                       # Backboard
            Rectangle((-250, -47.5), 500, 0, lw=1.5, ec=self.ec)                    # Baseline
        ]
        
        # Optional halfcourt elements
        if halfcourt:
            court_elements.extend([
                Arc((0, 422.5), 120, 120, theta1=180, theta2=0, lw=1.5, ec=self.ec), # Center arc
                Rectangle((-250, -47.5), 0, 470, lw=1.5, ec=self.ec),                 # Left sideline
                Rectangle((250, -47.5), 0, 470, lw=1.5, ec=self.ec),                  # Right sideline
                Rectangle((-250, 422.5), 500, 0, lw=1.5, ec=self.ec),                 # Halfway line
            ])

        # Draw all elements on the axis
        for element in court_elements:
            ax.add_patch(element)
        return ax

    def plot_shots(self, title_text="", subtitle_text="", show_picture=True, save_plot=False, save_plot_name="plot.png"):
        # Main plotting function for shots on the court
        fig, ax = plt.subplots(figsize=(12, 12))
        self.draw_court(ax=ax, moreyball=True)
        
        # Set font
        plt.rcParams['font.family'] = custom_font

        # Plot shots based on make or miss
        for i, edge_col in enumerate(['red', 'green']):
            marker_style = dict(fc=edge_col, ec=edge_col, s=150, alpha=0.4)
            ax.scatter(self.shots_df[self.shots_df.SHOT_MADE_FLAG == i].LOC_X, self.shots_df[self.shots_df.SHOT_MADE_FLAG == i].LOC_Y, **marker_style)
        
        # Set limits and hide axis lines
        ax.set_xlim(300, -300)
        ax.set_ylim(-100, 500)
        fig.patch.set_facecolor(self.bg)
        ax.axis('off')

        if not title_text:
            title_text = f"Shooting Chart — {self.player_name}"
        if not subtitle_text:
            subtitle_text =  f"{self.season} season"

        # Titles
        plt.text(250, 460, title_text, size='22', weight='semibold')
        plt.text(250, 440, subtitle_text, size='16')

        if show_picture:
            ax_image = fig.add_axes([0.72, 0.7659, 0.12, 0.12])
            ax_image.imshow(self.player_pic)
            ax_image.axis('off')

        if save_plot:
            plt.savefig(save_plot_name, bbox_inches="tight", pad_inches=0)