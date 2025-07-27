import numpy as np
from utils.geo import displacement_to_latlon
import xarray as xr
from pathlib import Path
from track.trackloader import DataChunk, build_cfg
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

        lats = self.traj['latitude']
        lons = self.traj['longitude']
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

        lats = self.traj['latitude']
        lons = self.traj['longitude']

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
                 traj_points: list['TrajPoint'] = None,
                 Datachunk: DataChunk = None):
        """
        Initialize a trajectory with a list of TrajPoint objects.
        :param traj_points: List of TrajPoint objects.
        """
        # Two init input will lead to conflict, raise an error
        self.chunks: list[DataChunk] = []
        self.envdata = {}
        # The continuous_chunk_list is used to store chunks of continuous trajectory points,
        # A chunk is a continuous trajectory coming from the same sheet source,
        # In a same chunk, DataChunk.get_point(i) can be replaced with ~.load_method().

        if traj_points is not None:
            if Datachunk is not None:
                raise ValueError(
                    "Cannot initialize Trajectory with both traj_points and Datachunk/sheet_path."
                )
            self.traj_points = traj_points
            self.data_info = self.traj2info()
            self.sheet_path = None

        elif Datachunk is not None:
            self.data_info = Datachunk
            self.traj_points = self.info2traj()
            self.sheet_path = Datachunk.path
            self.chunks.append(Datachunk)
        else:
            warnings.warn(
                "No traj_points or sheet_path provided, initializing empty trajectory.",
                UserWarning)
            self.traj_points = []
            self.data_info = None
            self.sheet_path = None

    def info2traj(self):
        """
        Optimized version to load all trajectory points from the data source in bulk.
        """
        length = self.data_info.cfg.length
        if length == 0:
            print("No TrajPoints in the trajectory to load.")
            return []

        cfg = self.data_info.cfg

        latitudes = self.data_info.get_data('latitude')
        longitudes = self.data_info.get_data('longitude')
        timestamps = self.data_info.get_data('timestamp')
        breakpoint()
        timestamps = pd.to_datetime(timestamps).to_numpy()
        primary_cols = {'latitude', 'longitude', 'timestamp'}
        other_keys = [
            key for key in cfg.header
            if key not in primary_cols and isinstance(cfg.header[key], int)
        ]
        other_data_cols = {
            key: self.data_info.get_data(key)
            for key in other_keys
        }

        data_dicts = [{
            key: other_data_cols[key][i]
            for key in other_keys
        } for i in range(length)]

        traj_points = [
            TrajPoint({
                'latitude': lat,
                'longitude': lon
            },
                      timestamp=ts,
                      data=data_dict) for lat, lon, ts, data_dict in tqdm(
                          zip(latitudes, longitudes, timestamps, data_dicts),
                          total=length,
                          desc="Loading TrajPoints (Optimized)",
                          unit="point")
        ]

        print(
            f"Loaded {len(traj_points)} TrajPoints from the trajectory info.")
        return traj_points

    def traj2info(self, path: str, cfgpath: str = './llm/data.yaml'):
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
        self.data_info = DataChunk(path,
                                   cfg=build_cfg(cfgpath),
                                   force_regeneration=True)

    def append(self, point: 'TrajPoint'):
        """
        Add a TrajPoint to the trajectory.
        :param point: TrajPoint object to add.
        """
        self.traj_points.append(point)
        #TODO: Implement chunking logic
        # self.continuous_chunk_list.append([point])
        # self.chunk_datapath_list.append(point.envdata)

    def setwinddata(self, datapath: str, engine='netcdf4'):
        """
        Set environment data for all TrajPoints in the trajectory.
        :param datapath: Path to the environment data file.
        :param engine: Engine to use for reading the data (default is 'netcdf4').
        """
        self.importEnv(key='u10', envfile=datapath, engine=engine)
        self.importEnv(key='v10', envfile=datapath, engine=engine)
        self.importEnv(key='u100', envfile=datapath, engine=engine)
        self.importEnv(key='v100', envfile=datapath, engine=engine)
        self.envdata['w10'] = np.sqrt(self.envdata['u10']**2 +
                                      self.envdata['v10']**2)
        self.envdata['w10_angle'] = np.arctan2(
            self.envdata['v10'], self.envdata['u10']) * 180 / np.pi
        self.envdata['w100'] = np.sqrt(self.envdata['u100']**2 +
                                       self.envdata['v100']**2)
        self.envdata['w100_angle'] = np.arctan2(
            self.envdata['v100'], self.envdata['u100']) * 180 / np.pi

        indices = self.chunk2index()
        for chunk, index in zip(self.chunks, indices):
            tqdm.pandas(desc="Setting w10 and w100 data for TrajPoints",
                        unit="point")
            for i, point in tqdm(enumerate(
                    self.traj_points[index[0]:index[1]]),
                                 total=index[1] - index[0]):
                point.setwind10(point.data['u10'], point.data['v10'])
                point.setwind100(point.data['u100'], point.data['v100'])
            print("Wind data set for all TrajPoints in the trajectory.")

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

    def importEnv(self, key: str, envfile: str, engine: str = 'cfgrib'):
        """
        Import environment data for all TrajPoints in the trajectory.
        This method is called automatically when setting environment data.
        """

        if not self.traj_points:
            print(
                "No TrajPoints in the trajectory to import environment data.")
            return
        indices = self.chunk2index()
        for chunk, index in zip(self.chunks, indices):
            time_coords = chunk.get_data('timestamp')
            lat_coords = chunk.get_data('latitude')
            lon_coords = chunk.get_data('longitude')
            time_coords = xr.DataArray(pd.to_datetime(time_coords).to_numpy(),
                                       dims='points')
            lat_coords = xr.DataArray(lat_coords, dims='points')
            lon_coords = xr.DataArray(lon_coords, dims='points')
            envdata = xr.open_dataset(envfile,
                                      engine=engine,
                                      decode_timedelta=True)
            interp_values = envdata[key].interp(latitude=lat_coords,
                                                longitude=lon_coords,
                                                time=time_coords).values
            self.envdata[key] = interp_values
            tqdm.pandas(desc=f"Importing {key} data for TrajPoints",
                        unit="point")
            for i, point in tqdm(enumerate(
                    self.traj_points[index[0]:index[1]]),
                                 total=index[1] - index[0]):
                point.setdata(key, interp_values[i])
        print(f"Imported environment data '{key}' for all TrajPoints.")

    def adhere(self, Traj: 'Trajectory'):
        """
        Adhere another trajectory to this one.
        :param Trajectory: The trajectory to adhere.
        """
        #TODO: Implement adherence logic
        if not isinstance(Traj, Trajectory):
            raise TypeError("Trajectory must be an instance of 'Trajectory'.")
        self.traj_points.extend(Traj.traj_points)
        self.data_info = self.traj2info(self.sheet_path)
        self.continuous_chunk_list += Traj.continuous_chunk_list
        self.chunk_datapath_list += Traj.chunk_datapath_list
        print(f"Adhered {len(Traj.traj_points)} points to the trajectory.")

    def chunk2index(self):
        """

        Convert the continuous chunk list to a list of indices.
        :return: List of indices corresponding to the continuous chunks.
        """
        indices = []
        end = 0
        for chunk in self.chunks:
            start = end
            end += chunk.cfg.length
            indices.append((start, end))
        return indices

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
            if identifier in self.envdata:
                result.extend(self.envdata[identifier])
                return np.array(result)
            for chunk in self.chunks:
                if identifier not in chunk.cfg.header:
                    raise KeyError(
                        f"Identifier '{identifier}' not found in trajectory chunks."
                    )
                else:
                    result.extend(chunk.get_data(identifier))
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
