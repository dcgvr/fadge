# Copyright (C) 2020,2022 Chi-kwan Chan
# Copyright (C) 2020,2022 Steward Observatory
#
# This file is part of fadge.
#
# Fadge is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fadge is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fadge.  If not, see <http://www.gnu.org/licenses/>.


from jax import numpy as np
from jax.experimental.maps import xmap

from .metric import KerrSchild
from .geode  import Geode
from .utils  import Nullify, Normalize
from .icond  import cam, sphorbit


class GRRT:

    def __init__(self, aspin=0, qcharge=0, hp=False, dtype=np.float32, **kwargs):
        self.aspin   = aspin
        self.qcharge = qcharge
        self.dtype   = dtype
        self.kwargs  = kwargs

        self.metric    = KerrSchild(aspin, qcharge)
        self.nullify   = Nullify(self.metric)
        self.normalize = Normalize(self.metric)

        self.reh    = np.nan
        self._geode = None
        self._ic    = None

        aa = self.aspin   * self.aspin
        qq = self.qcharge * self.qcharge
        if aa <= 1:
            reh = 1.0 + np.sqrt(1 - aa - qq)
            print('Radius of outer event horizon:', reh)
            if hp:
                print('Horizon penetrating')
            else:
                self.reh = reh
        else:
            print('There is no event horizon')

        def KSr(x): # closure on aa
            zz = x[3] * x[3]
            kk = 0.5 * (x[1] * x[1] + x[2] * x[2] + zz - aa)
            rr = np.sqrt(kk * kk + aa * zz) + kk
            return np.sqrt(rr)
        self.KSr = KSr

        def KSd(x): # closure on aspin
            dR = np.sqrt(x[1] * x[1] + x[2] * x[2]) - abs(aspin)
            return np.sqrt(dR * dR + x[3] * x[3])
        self.KSd = KSd

    def set_particle(self, x, v):
        x = np.asarray(x)
        v = np.asarray(v)
        self._ic    = np.array([x, self.normalize(x, v)])
        self.kwargs = {'L':100, 'h':1, **self.kwargs}

    def set_photon(self, x, v):
        x = np.asarray(x)
        v = np.asarray(v)
        self._ic    = np.array([x, self.nullify(x, v)])
        self.kwargs = {'L':100, 'h':1, **self.kwargs}

    def set_sphorbit(self, r=3):
        s = sphorbit(self.aspin, r)
        self._ic    = np.array([s[0], self.nullify(s[0],s[1])])
        self.kwargs = {'L':100, 'h':1, **self.kwargs}

    def set_cam(self, r_obs=1e4, i_obs=60, j_obs=0):
        self.rij    = np.array([r_obs, np.radians(i_obs), np.radians(j_obs)], dtype=self.dtype)
        self.kwargs = {'L':-2*r_obs, 'h':0.75*r_obs, **self.kwargs}

    def set_pixels(self, a, b):
        def ic(ab): # closure on self.rij and self.nullify
            s = cam(self.rij, ab)
            return np.array([s[0], self.nullify(s[0],s[1])], dtype=ab.dtype)
        ab = np.array([a, b], dtype=self.dtype)
        self._ic = xmap(
            ic,
            in_axes ={i  :i for i in range(1,ab.ndim)},
            out_axes={i+1:i for i in range(1,ab.ndim)},
        )(ab)

    def set_image(self, fov=16, n=32, alpha0=0, beta0=0):
        axes = fov * ((np.arange(n) + 0.5) / n - 0.5)
        a, b = np.meshgrid(axes+alpha0, axes+beta0, indexing='ij')
        self.set_pixels(a, b)

    def set_axis(self, fov=16, n=32, PA=90, alpha0=0):
        r = fov * ((np.arange(n) + 0.5) / n - 0.5) + alpha0
        a = r * np.sin(PA * np.pi / 180)
        b = r * np.cos(PA * np.pi / 180)
        self.set_pixels(a, b)

    def set_ring(self, r=5.2, n=32):
        phi = 2 * np.pi * np.arange(n) / n
        a   = r * np.cos(phi)
        b   = r * np.sin(phi)
        self.set_pixels(a, b)

    def geode(self, L=None, N=None, **kwargs):

        if self._ic is not None:
            kwargs = {'dtype':self.dtype, **self.kwargs, **kwargs} # compose kwargs
            if L is not None:
                kwargs.pop('L')

            fhupper = kwargs.pop('fhupper', 0.75)
            if 'hupper' not in kwargs:
                kwargs['hupper'] = lambda l, s: self.KSr(s[0]) * fhupper + 1

            fhlower = kwargs.pop('fhlower', None)
            if 'hlower' not in kwargs and fhlower is not None:
                kwargs['hlower'] = lambda l, s: fhlower

            eps = kwargs.pop('eps', 1e-2)
            if 'filter' not in kwargs:
                if np.isnan(self.reh):
                    kwargs['filter'] = lambda l, s: self.KSd(s[0]) >= eps
                else:
                    kwargs['filter'] = lambda l, s: self.KSr(s[0]) >= self.reh + eps

            self._geode = Geode(self.metric, 0, self._ic, **kwargs)
            self._ic    = None
        elif len(kwargs) > 0:
            print('Warning: ignore `kwargs`')

        if L is None:
            L = self.kwargs['L']
        try:
            len(L)
        except: # L is a scalar
            self._geode.extend(L, N=N)
            return self._geode.lambdas, self._geode.states
        else:   # L is not a scalar
            return self._geode(L, N=N)
