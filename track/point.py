import numpy as np
import xarray as xr
from utils.geo import displacement_to_latlon
import warnings


class TrajPoint:

    def __init__(self,
                 location: dict,
                 timestamp: np.datetime64,
                 data: dict = None):
        # location, timestamp
        # **states: speed: float, sail_state: int, DG_state: int, SOC: float, fuel: float
        # location: dict, {'lat': float, 'lon': float}
        self.location = location
        self.latitude = location['latitude']
        self.longitude = location['longitude']
        self.timestamp = timestamp
        self.parent = None
        self.envdata = None
        self.data = {}
        self.wind_u, self.wind_v = None, None
        self.data['latitude'] = self.latitude
        self.data['longitude'] = self.longitude
        self.data['timestamp'] = self.timestamp
        for key, value in data.items():
            self.data[key] = value

    @classmethod
    def follow(cls, parent, disp, dt):
        '''
        parent: TrajPoint, 上级节点
        disp: [dx, dy], 位移, m
        dt: 时间间隔, s
        '''
        new_lat, new_lon = displacement_to_latlon(parent.latitude,
                                                  parent.longitude, disp[0],
                                                  disp[1])
        new_timestamp = parent.timestamp + np.timedelta64(dt, 's')

        new_node = TrajPoint({
            'latitude': new_lat,
            'longitude': new_lon
        }, new_timestamp)
        new_node.parent = parent
        new_node.envdata = parent.envdata
        new_node.setwind()
        return new_node

    def parent(self, parent: 'TrajPoint'):
        self.parent = parent

    def __str__(self):
        return f"TrajPoint: {self.location}, {self.timestamp}"

    def update(self, **states):
        for key, value in states.items():
            setattr(self, key, value)

    def set_env_data(self, datapath: str, engine='netcdf4'):
        self.envdata = xr.open_dataset(datapath,
                                       engine=engine,
                                       decode_timedelta=True)
        self.importEnv()

    def setdata(self, key, value):
        """
        Set data for a specific key.
        """
        self.data[key] = value

    def setwind10(self, u10, v10):
        """
        Set wind data at 10m height.
        """

        self.data['w10'] = np.sqrt(u10**2 + v10**2)
        self.data['w10_angle'] = np.arctan2(v10, u10) * 180 / np.pi

    def setwind100(self, u100, v100):
        """
        Set wind data at 100m height.
        """

        self.data['w100'] = np.sqrt(u100**2 + v100**2)
        self.data['w100_angle'] = np.arctan2(v100, u100) * 180 / np.pi

    def importEnv(self):

        if self.envdata is None:
            print('No data, run TrajPoint.setdata(xr.Dataset:data) first')
            return

        if 'u10' not in self.envdata or 'v10' not in self.envdata:
            print('No wind data @ 10m, run TrajPoint.setwind() first')
            return

        else:
            self.u10 = self.envdata['u10'].interp(latitude=self.latitude,
                                                  longitude=self.longitude,
                                                  time=self.timestamp).values
            self.v10 = self.envdata['v10'].interp(latitude=self.latitude,
                                                  longitude=self.longitude,
                                                  time=self.timestamp).values
            self.data['u10'] = self.u10
            self.data['v10'] = self.v10
            self.data['w10'] = np.sqrt(self.u10**2 + self.v10**2)
            self.data['w10_angle'] = np.arctan2(self.v10,
                                                self.u10) * 180 / np.pi
        if 'u100' in self.envdata and 'v100' in self.envdata:
            self.u100 = self.envdata['u100'].interp(latitude=self.latitude,
                                                    longitude=self.longitude,
                                                    time=self.timestamp).values
            self.v100 = self.envdata['v100'].interp(latitude=self.latitude,
                                                    longitude=self.longitude,
                                                    time=self.timestamp).values
            self.data['u100'] = self.u100
            self.data['v100'] = self.v100
            self.data['w100'] = np.sqrt(self.u100**2 + self.v100**2)
            self.data['w100_angle'] = np.arctan2(self.v100,
                                                 self.u100) * 180 / np.pi

    def useEnv(self, warning=True):

        if warning:
            warnings.warn(
                'This will force self.wind_u=self.u10, self.wind_v=self.v10',
                UserWarning)
        if self.envdata is None:
            print('No data, run TrajPoint.setdata(xr.Dataset:data) first')
            return
        self.wind_u = self.u10
        self.wind_v = self.v10

    def wind(self):
        """
        Returns the wind speed and direction at the TrajPoint's location.
        """
        warnings.warn('Deprecated, directly use self.wind_u and self.wind_v',
                      DeprecationWarning)
        if self.wind_u is None or self.wind_v is None:
            print('No wind, run TrajPoint.setwind() first')
            return
        else:
            return np.sqrt(self.wind_u**2 + self.wind_v**2)

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
