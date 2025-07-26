import numpy as np
from utils.geo import displacement_to_latlon
import xarray as xr
from pathlib import Path
from track.trackloader import DataInfoExtractor
from track.point import TrajPoint
import warnings
import pandas as pd
from tqdm.rich import tqdm


class TrajVizContainer:

    def __init__(self, traj: 'Trajectory', engine: str):
        """
        Initialize a TrajVizContainer with a Trajectory object.
        :param traj: Trajectory object to visualize.
        """
        MATPLOTLIB = 'matplotlib'
        PLOTLY = 'plotly'
        WEB = 'web'
        ALL_ENGINES = [MATPLOTLIB, PLOTLY, WEB]
        METHODS = [self.plot_matplotlib, self.plot_plotly, self.plot_web]
        self.traj = traj
        self.engine = engine
        if not isinstance(self.traj, Trajectory):
            raise TypeError("traj must be an instance of Trajectory.")
        if self.engine not in ALL_ENGINES:
            raise ValueError(
                f"Invalid engine type: {self.engine}. Must be one of {ALL_ENGINES}."
            )
        self.method = METHODS[ALL_ENGINES.index(self.engine)]

    def plot(self, show: bool = True):
        """
        Plots the trajectory using the specified engine.
        """
        self.method(show=show)

    def plot_matplotlib(self, show: bool = True):
        """
        Plot the trajectory using Matplotlib.
        """
        import matplotlib.pyplot as plt
        from mpl_toolkits.basemap import Basemap

        fig, ax = plt.subplots(figsize=(10, 10))
        m = Basemap(projection='merc', resolution='i', ax=ax)
        m.drawcoastlines()
        m.drawcountries()
        m.drawmapboundary(fill_color='aqua')
        m.fillcontinents(color='lightgray', lake_color='aqua')

        lats = [point.latitude for point in self.traj.traj_points]
        lons = [point.longitude for point in self.traj.traj_points]
        x, y = m(lons, lats)

        m.plot(x, y, marker='o', color='red', markersize=5, linewidth=2)
        plt.title('Trajectory Visualization')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.savefig(
            Path(self.traj.data_info.path).parent / 'trajectory_plot.png')
        if show:
            plt.show()

    def plot_plotly(self, show: bool = True):
        """
        Plot the trajectory using Plotly.
        """
        import plotly.graph_objects as go

        lats = [point.latitude for point in self.traj.traj_points]
        lons = [point.longitude for point in self.traj.traj_points]

        fig = go.Figure(data=go.Scattergeo(lon=lons,
                                           lat=lats,
                                           mode='markers+lines',
                                           marker=dict(size=5, color='red'),
                                           line=dict(width=2, color='blue'),
                                           name='Trajectory'))

        fig.update_layout(title='Trajectory Visualization',
                          geo=dict(scope='world',
                                   showland=True,
                                   landcolor='lightgray',
                                   showlakes=True,
                                   lakecolor='aqua'))
        fig.write_html(
            Path(self.traj.data_info.path).parent / 'trajectory_plot.html')
        if show:
            fig.show()

    def plot_web(self, show: bool = True):
        # Charts interface, Geo map interface, etc.
        pass


class Trajectory:

    def __init__(self,
                 sheet_path: str = None,
                 traj_points: list['TrajPoint'] = None,
                 DataInfo: DataInfoExtractor = None):
        """
        Initialize a trajectory with a list of TrajPoint objects.
        :param traj_points: List of TrajPoint objects.
        """
        # Two init input will lead to conflict, raise an error

        if traj_points is not None:
            if DataInfo is not None and sheet_path is not None:
                raise ValueError(
                    "Cannot initialize Trajectory with both traj_points and DataInfo/sheet_path."
                )
            self.traj_points = traj_points
            self.data_info = self.traj2info()
            self.sheet_path = None

        elif sheet_path is not None:
            if DataInfo is not None:
                raise ValueError(
                    "Cannot initialize Trajectory with both sheet_path and traj_points/DataInfo."
                )
            self.sheet_path = Path(sheet_path).resolve()
            self.data_info = DataInfoExtractor(self.sheet_path,
                                               force_regeneration=True)
            self.traj_points = self.info2traj()
        elif DataInfo is not None:
            self.data_info = DataInfo
            self.traj_points = self.info2traj()
            self.sheet_path = DataInfo.path
        else:
            warnings.warn(
                "No traj_points or sheet_path provided, initializing empty trajectory.",
                UserWarning)
            self.traj_points = []
            self.data_info = None
            self.sheet_path = None

    def info2traj(self):
        length = self.data_info.cfg.length
        if length == 0:
            print("No TrajPoints in the trajectory to load.")
            return []
        traj_points = []
        for i in tqdm(range(length),
                      desc="Loading TrajPoints",
                      leave=False,
                      unit="point"):
            point = self.data_info.get_point(i)
            traj_points.append(point)
        print(
            f"Loaded {len(traj_points)} TrajPoints from the trajectory info.")
        return traj_points

    def traj2info(self, path: str):
        """
        Save the trajectory points to a CSV file.
        :param path: Path to save the CSV file.
        """
        if not self.traj_points:
            print("No TrajPoints in the trajectory to save.")
            return
        geodata = {
            'latitude': [point.latitude for point in self.traj_points],
            'longitude': [point.longitude for point in self.traj_points],
            'timestamp': [point.timestamp for point in self.traj_points]
        }
        envdata = {
            'wind_u': [point.wind_u for point in self.traj_points],
            'wind_v': [point.wind_v for point in self.traj_points],
            'u10': [
                point.envdata['u10'].values if point.envdata else None
                for point in self.traj_points
            ],
            'v10': [
                point.envdata['v10'].values if point.envdata else None
                for point in self.traj_points
            ],
            'u100': [
                point.envdata['u100'].values if point.envdata else None
                for point in self.traj_points
            ],
            'v100': [
                point.envdata['v100'].values if point.envdata else None
                for point in self.traj_points
            ]
        }
        other_data_keys = self.traj_points[0].data.keys(
        ) if self.traj_points else []
        other_data = {
            key: [point.data.get(key, None) for point in self.traj_points]
            for key in other_data_keys
        }
        df = pd.DataFrame({**geodata, **envdata, **other_data})
        df.to_csv(path, index=False)
        print(f"Trajectory saved to {path}")
        self.data_info = DataInfoExtractor(self.sheet_path,
                                           force_regeneration=True)

    def append(self, point: 'TrajPoint'):
        """
        Add a TrajPoint to the trajectory.
        :param point: TrajPoint object to add.
        """
        self.traj_points.append(point)

    def setenvdata(self, datapath: str, engine='netcdf4'):
        """
        Set environment data for all TrajPoints in the trajectory.
        :param datapath: Path to the environment data file.
        :param engine: Engine to use for reading the data (default is 'netcdf4').
        """
        warnings.warn(
            "This will *remove all linked environment data* in TrajPoints and set new data.",
            UserWarning)
        print("I will set new environment data for all TrajPoints. [y/n]")
        if input().lower() != 'y':
            print("Aborted setting environment data.")
            return
        if not self.traj_points:
            print("No TrajPoints in the trajectory to set environment data.")
            return
        print(
            f"Setting environment data for {len(self.traj_points)} TrajPoints from {datapath} using engine {engine}."
        )
        for point in self.traj_points:
            point.set_env_data(datapath, engine)

    def useEnv(self, warning=True):
        """
        Use the environment data for all TrajPoints in the trajectory.
        :param warning: If True, will show a warning about using environment data.
        """
        if warning:
            warnings.warn(
                'This method *assumes* that the GroundTruth wind data is *exactly* the same as the wind data on the ship.',
                UserWarning)
        if not self.traj_points:
            print('No TrajPoints in the trajectory to use environment data.')
            return
        for point in self.traj_points:
            point.useEnv(warning=False)

    def __getitem__(self, identifier):
        """
        Get a TrajPoint by index.
        :param index: Index of the TrajPoint to retrieve.
        :return: TrajPoint object at the specified index.
        """
        if isinstance(identifier, int):
            return self.traj_points[identifier]
        elif isinstance(identifier, str):
            result = []
            for point in self.traj_points:
                if identifier not in point.data:
                    warnings.warn(
                        f"TrajPoint {point} does not have data for key '{identifier}', replacing with None."
                    )
                    result.append(None)
                result.append(point.data[identifier])
            result = np.array(result)
            if len(result) == 1:
                return result[0]
            elif len(result) == 0:
                raise KeyError(f"No TrajPoint found with key '{identifier}'.")
            else:
                return result
        elif isinstance(identifier, list):
            print('Creating a new Trajectory subset with specified indices.')
            if not all(isinstance(i, int) for i in identifier):
                raise ValueError(
                    "Identifier must be a list of integer indices.")
            if any(i < 0 or i >= len(self.traj_points) for i in identifier):
                raise IndexError(
                    "Identifier indices are out of bounds for the trajectory.")
            # Create a new Trajectory object with the specified points
            # This assumes TrajPoint objects are hashable and can be used in a list
            return Trajectory(
                traj_points=[self.traj_points[i] for i in identifier])
        else:
            raise TypeError(
                "Identifier must be an integer index, a string key, or a list of indices."
            )

    def __iter__(self):
        """
        Make the Traj object iterable.
        :return: Iterator over TrajPoint objects.
        """
        return iter(self.traj_points)

    def __str__(self):
        return f"Trajectory with {len(self.traj_points)} points"
