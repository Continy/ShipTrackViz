import numpy as np
from utils.geo import displacement_to_latlon
import xarray as xr


class TrajPoint:

    def __init__(self, location: dict, timestamp: np.datetime64):
        # location, timestamp
        # **states: speed: float, sail_state: int, DG_state: int, SOC: float, fuel: float
        # location: dict, {'lat': float, 'lon': float}
        self.location = location
        self.latitude = location['lat']
        self.longitude = location['lon']
        self.timestamp = timestamp
        self.father = None
        self.data = None
        self.wind_u, self.wind_v = None, None

    @classmethod
    def follow(cls, father, disp, dt):
        '''
        father: ShipNode, 父节点
        disp: [dx, dy], 位移, m
        dt: 时间间隔, s
        '''
        new_lat, new_lon = displacement_to_latlon(father.latitude,
                                                  father.longitude, disp[0],
                                                  disp[1])
        new_timestamp = father.timestaSHmp + np.timedelta64(dt, 's')

        new_node = TrajPoint({'lat': new_lat, 'lon': new_lon}, new_timestamp)
        new_node.father = father
        new_node.data = father.data
        new_node.setwind()
        return new_node

    def father(self, father: 'TrajPoint'):
        self.father = father

    def __str__(self):
        return f"ShipNode: {self.location}, {self.timestamp}"

    def update(self, **states):
        for key, value in states.items():
            setattr(self, key, value)

    def setdata(self, datapath: str, engine='netcdf4'):
        self.data = xr.open_dataset(datapath, engine=engine)

    def setwind(self):
        if self.data is None:
            print('No data, run ShipNode.setdata(xr.Dataset:data) first')
            return
        else:
            self.wind_u = self.data['u10'].interp(latitude=self.latitude,
                                                  longitude=self.longitude,
                                                  time=self.timestamp).values
            self.wind_v = self.data['v10'].interp(latitude=self.latitude,
                                                  longitude=self.longitude,
                                                  time=self.timestamp).values

    def sail_params(self, u, v):
        '''
        u: float, 东向船速
        v: float, 北向船速
        return: tuple, (phi_omega(rad), V_wap(m/s))
        '''
        if self.wind_u is None:
            print('No wind, run ShipNode.setwind() first')
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
        'lat': 19.5,
        'lon': 111.
    }, np.array('2022-01-01T12:00:00', dtype='datetime64[ns]'))

    ship_u = 10
    ship_v = 2
    ship_1.setdata('nc/other2022.nc')
    ship_1.setwind()
    ship_1.sail_params(ship_u, ship_v)
    print(ship_1.timestamp)
    print(ship_1.location)
    print(ship_1.wind_u, ship_1.wind_v)
    ship_2 = TrajPoint.follow(ship_1, disp=[64800, 0], dt=64800)
    print(ship_2.location)
    print(ship_2.timestamp)
    print(ship_2.wind_u, ship_2.wind_v)
