import numpy as np
from utils.geo import displacement_to_latlon
import xarray as xr
from pathlib import Path
from track.trackloader import DataInfoExtractor
import warnings
import pandas as pd


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
        length = self.data_info.length
        if length == 0:
            print("No TrajPoints in the trajectory to load.")
            return []
        traj_points = []
        for i in range(length):
            point_data = self.data_info.get_point(i)
            if point_data is None:
                warnings.warn(
                    f"TrajPoint at index {i} is None, skipping this point.",
                    UserWarning)
                continue
            point = TrajPoint(
                {
                    'latitude': point_data['latitude'],
                    'longitude': point_data['longitude']
                },
                pd.to_datetime(point_data['timestamp']).to_numpy())
            point.wind_u = point_data['wind_u']
            point.wind_v = point_data['wind_v']
            point.envdata = point_data['envdata']
            point.data = point_data['data']
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


class TrajPoint:

    def __init__(self, location: dict, timestamp: np.datetime64):
        # location, timestamp
        # **states: speed: float, sail_state: int, DG_state: int, SOC: float, fuel: float
        # location: dict, {'lat': float, 'lon': float}
        self.location = location
        self.latitude = location['latitude']
        self.longitude = location['longitude']
        self.timestamp = timestamp
        self.father = None
        self.envdata = None
        self.data = {}
        self.wind_u, self.wind_v = None, None

    @classmethod
    def follow(cls, father, disp, dt):
        '''
        father: TrajPoint, 父节点
        disp: [dx, dy], 位移, m
        dt: 时间间隔, s
        '''
        new_lat, new_lon = displacement_to_latlon(father.latitude,
                                                  father.longitude, disp[0],
                                                  disp[1])
        new_timestamp = father.timestamp + np.timedelta64(dt, 's')

        new_node = TrajPoint({
            'latitude': new_lat,
            'longitude': new_lon
        }, new_timestamp)
        new_node.father = father
        new_node.envdata = father.envdata
        new_node.setwind()
        return new_node

    def father(self, father: 'TrajPoint'):
        self.father = father

    def __str__(self):
        return f"TrajPoint: {self.location}, {self.timestamp}"

    def update(self, **states):
        for key, value in states.items():
            setattr(self, key, value)

    def set_env_data(self, datapath: str, engine='netcdf4'):
        self.envdata = xr.open_dataset(datapath, engine=engine)

    def setdata(self, key, value):
        """
        Set data for a specific key.
        """
        self.data[key] = value

    def useEnv(self):
        warnings.warn(
            'This method *assumes* that the GroundTruth wind data is *exactly* the same as the wind data on the ship.',
            UserWarning)
        if self.envdata is None:
            print('No data, run TrajPoint.setdata(xr.Dataset:data) first')
            return
        else:
            self.wind_u = self.envdata['u10'].interp(
                latitude=self.latitude,
                longitude=self.longitude,
                time=self.timestamp).values
            self.wind_v = self.envdata['v10'].interp(
                latitude=self.latitude,
                longitude=self.longitude,
                time=self.timestamp).values

    def sail_params(self, u, v):
        '''
        u: float, 东向船速
        v: float, 北向船速
        return: tuple, (phi_omega(rad), V_wap(m/s))
        '''
        if self.wind_u is None:
            print('No wind, run TrajPoint.setwind() first')
            return
        else:
            return self._calculate_sail_params((u, v),
                                               (self.wind_u, self.wind_v))

    def _calculate_sail_params(self, a, b):
        # 计算向量c: c = -(a + b)
        c = -(np.array(a) + np.array(b))

        # 计算a和c之间的余弦值
        cos_theta = np.dot(a, c) / (np.linalg.norm(a) * np.linalg.norm(c))

        # 计算phi_omega: phi_omega = pi - cos_theta
        # 注意acos返回的是弧度值
        phi_omega = np.pi - cos_theta

        return c, phi_omega


if __name__ == '__main__':
    ship_1 = TrajPoint({
        'latitude': 17.2,
        'longitude': 115.5
    }, np.array('2024-02-04T12:00:00', dtype='datetime64[ns]'))

    ship_u = 10
    ship_v = 2
    ship_1.setdata('/data/split/data.grib', engine='cfgrib')
    ship_1.setwind()
    ship_1.sail_params(ship_u, ship_v)
    print(ship_1.timestamp)
    print(ship_1.location)
    print(ship_1.wind_u, ship_1.wind_v)
    ship_2 = TrajPoint.follow(ship_1, disp=[64800, 0], dt=64800)
    print(ship_2.location)
    print(ship_2.timestamp)
    print(ship_2.wind_u, ship_2.wind_v)
