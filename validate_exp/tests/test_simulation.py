# Python 2 compatibility
from __future__ import print_function
from __future__ import division

import os
import pkg_resources
import numpy as np
import pytest

# Related modules
try:
    import cantera as ct
except ImportError:
    print("Error: Cantera must be installed.")
    raise

from .. import simulation
from .. import parse_files

class TestToKelvin:
    """Class of tests for function that converts temperature to Kelvin.
    """
    def test_kelvin_to_kelvin(self):
        temp = simulation.to_kelvin(300., 'K')
        np.testing.assert_allclose(temp, 300.)

    def test_celsius_to_kelvin(self):
        temp = simulation.to_kelvin(1000., 'C')
        np.testing.assert_allclose(temp, 1273.15)

    def test_farenheit_to_kelvin(self):
        temp = simulation.to_kelvin(32., 'F')
        np.testing.assert_allclose(temp, 273.15)

    def test_negative_kelvin(self):
        with pytest.raises(ValueError):
            temp = simulation.to_kelvin(-1., 'K')

    def test_units_error(self):
        with pytest.raises(KeyError):
            temp = simulation.to_kelvin(300., 'R')


class TestFirstDerivative:
    """
    """
    def test_derivative_zero(self):
        """Tests first derivative for zero change.
        """
        n = 5
        x = np.arange(n)
        y = np.ones(n)
        dydx = simulation.first_derivative(x, y)
        np.testing.assert_array_equal(np.zeros(n), dydx)

    def test_derivative_one(self):
        """Tests unity first derivative.
        """
        n = 5
        x = np.arange(n)
        y = np.arange(n)
        dydx = simulation.first_derivative(x, y)
        np.testing.assert_array_equal(np.ones(n), dydx)

    def test_derivative_sin(self):
        """Tests derivative of sin.
        """
        x = np.arange(0., 10., 0.001)
        dydx = simulation.first_derivative(x, np.sin(x))
        np.testing.assert_array_almost_equal(dydx, np.cos(x))


class TestSampleRisingPressure:
    """
    """
    def test_sample_pressure_no_rise(self):
        """Test that pressure sampled correctly with no rise.
        """
        time_end = 10.0
        pres = 1.0
        pres_rise = 0.0
        freq = 2.e4
        [times, pressures] = simulation.sample_rising_pressure(time_end, pres,
                                                               freq, pres_rise
                                                               )
        # Check time array
        assert len(times) == int(freq * time_end + 1)
        assert times[-1] == time_end

        # Ensure pressure all equal to initial pressure
        np.testing.assert_allclose(pressures, pres)

    def test_sample_pressure_rise(self):
        """Test that pressure sampled correctly with rise.
        """
        time_end = 10.0
        pres = 1.0
        pres_rise = 0.05
        freq = 2.e4
        [times, pressures] = simulation.sample_rising_pressure(time_end, pres,
                                                               freq, pres_rise
                                                               )
        # Check time array
        assert len(times) == int(freq * time_end + 1)
        assert times[-1] == time_end

        # Ensure final pressure correct, and check constant derivative
        np.testing.assert_allclose(pressures[-1],
                                   pres*(pres_rise * time_end + 1)
                                   )
        dpdt = simulation.first_derivative(times, pressures)
        np.testing.assert_allclose(dpdt, pres * pres_rise)


class TestCreateVolumeHistory:
    """
    """
    def test_volume_profile_no_pressure_rise(self):
        """Ensure constant volume history if zero pressure rise.
        """
        [times, volume] = simulation.create_volume_history(
                    'air.xml', 300., ct.one_atm, 'N2:1.0', 0.0, 1.0
                    )
        # check that end time is correct and volume unchanged
        np.testing.assert_approx_equal(times[-1], 1.0)
        np.testing.assert_allclose(volume, 1.0)

    def test_artificial_volume_profile_nitrogen(self):
        """Check correct volume profile for nitrogen mixture.
        """
        initial_pres = 1.0 * ct.one_atm
        pres_rise = 0.05
        end_time = 1.0
        initial_temp = 300.
        [times, volumes] = simulation.create_volume_history(
                    'air.xml', initial_temp, initial_pres, 'N2:1.0',
                    pres_rise, end_time
                    )
        # pressure at end time
        end_pres = initial_pres * (pres_rise * end_time + 1.0)

        gas = ct.Solution('air.xml')
        gas.TPX = initial_temp, initial_pres, 'N2:1.0'
        initial_density = gas.density

        # assume specific heat ratio roughly constant
        gamma = gas.cp / gas.cv
        volume = ((end_pres / initial_pres)**(-1. / gamma))

        # check that end time is correct and volume matches expected
        np.testing.assert_allclose(times[-1], 1.0)
        np.testing.assert_allclose(volume, volumes[-1], rtol=1e-5)


class TestVolumeProfile:
    """
    """
    def test_zero_velocity_after_end(self):
        """Ensure volume profile returns zero velocity after end of time series.
        """
        tmax = 10.
        times = np.arange(0, tmax, 0.001)
        volumes = np.cos(times)

        properties = {}
        properties['time'] = simulation.Property(times, 's')
        properties['volume'] = simulation.Property(volumes, 'cm^3')
        volume_profile = simulation.VolumeProfile(properties)

        assert volume_profile(tmax + 1.) == 0.

    def test_interpolated_velocity(self):
        """Ensure volume profile returns correct interpolated velocity.
        """
        tmax = 10.
        times = np.arange(0, tmax, 0.001)
        volumes = np.cos(times)

        properties = {}
        properties['time'] = simulation.Property(times, 's')
        properties['volume'] = simulation.Property(volumes, 'cm^3')
        velocity_profile = simulation.VolumeProfile(properties)

        np.testing.assert_allclose(velocity_profile(np.pi), -np.sin(np.pi),
                                   rtol=1e-7, atol=1e-10
                                   )


class TestPressureRiseProfile:
    """
    """
    def test_artificial_volume_profile(self):
        """
        """
        init_temp = 300.
        init_pressure = 1.0 * ct.one_atm
        pressure_rise = 0.05
        end_time = 10.0

        velocity_profile = simulation.PressureRiseProfile(
            'air.xml', init_temp, init_pressure, 'N2:1.0',
            pressure_rise, end_time
            )

        # Sample pressure
        [times, pressures] = simulation.sample_rising_pressure(
            end_time, init_pressure, 2.e3, pressure_rise)

        # Check velocity profile against "theoretical" volume derivative
        gas = ct.Solution('air.xml')
        gas.TPX = init_temp, init_pressure, 'N2:1.0'
        init_entropy = gas.entropy_mass
        velocities = np.zeros(pressures.size)
        dvolumes = np.zeros(pressures.size)
        for i in range(pressures.size):
            gas.SP = init_entropy, pressures[i]
            gamma = gas.cp / gas.cv
            velocities[i] = velocity_profile(times[i])
            dvolumes[i] = ((-1. / gamma) * pressure_rise *
                           (pressures[i] / init_pressure)**((-1. / gamma) - 1.0)
                           )

        np.testing.assert_allclose(velocities, dvolumes, rtol=1e-3)


class TestSimulation:
    """Group of tests on `Simulation` class.
    """
    def test_shock_tube_setup_case(self):
        """Test that shock tube cases are set up properly.
        """
        file_path = os.path.join('testfile_st.xml')
        filename = pkg_resources.resource_filename(__name__, file_path)
        properties = parse_files.read_experiment(filename)

        # Now create list of Simulation objects
        simulations = parse_files.create_simulations(properties)

        assert len(simulations) == 2

        mechanism_filename = 'gri30.xml'
        spec_key = {'H2': 'H2', 'O2': 'O2', 'N2': 'N2', 'Ar': 'AR'}

        gas = ct.Solution(mechanism_filename)

        sim = simulations[0]
        sim.setup_case(mechanism_filename, spec_key)

        assert sim.kind == 'ST'
        np.testing.assert_allclose(sim.time_end, 4.7154e-3)
        np.testing.assert_allclose(sim.gas.T, 1164.48)
        np.testing.assert_allclose(sim.gas.P, 2.18 * ct.one_atm)
        mass_fracs = np.zeros(sim.gas.n_species)
        mass_fracs[sim.gas.species_index(spec_key['H2'])] = 0.00444
        mass_fracs[sim.gas.species_index(spec_key['O2'])] = 0.00566
        mass_fracs[sim.gas.species_index(spec_key['Ar'])] = 0.9899
        np.testing.assert_allclose(sim.gas.X, mass_fracs)
        # no wall velocity
        times = np.linspace(0., sim.time_end, 100)
        for time in times:
            np.testing.assert_allclose(sim.reac.walls[0].vdot(time), 0.0)
        assert sim.n_vars == gas.n_species + 3

        sim = simulations[1]
        sim.setup_case(mechanism_filename, spec_key)

        assert sim.kind == 'ST'
        np.testing.assert_allclose(sim.time_end, 4.4803e-3)
        np.testing.assert_allclose(sim.gas.T, 1164.97)
        np.testing.assert_allclose(sim.gas.P, 2.18 * ct.one_atm)
        mass_fracs = np.zeros(sim.gas.n_species)
        mass_fracs[sim.gas.species_index(spec_key['H2'])] = 0.00444
        mass_fracs[sim.gas.species_index(spec_key['O2'])] = 0.00566
        mass_fracs[sim.gas.species_index(spec_key['Ar'])] = 0.9899
        np.testing.assert_allclose(sim.gas.X, mass_fracs)
        # no wall velocity
        times = np.linspace(0., sim.time_end, 100)
        for time in times:
            np.testing.assert_allclose(sim.reac.walls[0].vdot(time), 0.0)
        assert sim.n_vars == gas.n_species + 3

    def test_shock_tube_pressure_rise_setup_case(self):
        """Test that shock tube case with pressure rise is set up properly.
        """
        file_path = os.path.join('testfile_st2.xml')
        filename = pkg_resources.resource_filename(__name__, file_path)
        properties = parse_files.read_experiment(filename)

        # Now create list of Simulation objects
        simulations = parse_files.create_simulations(properties)

        assert len(simulations) == 1

        mechanism_filename = 'gri30.xml'
        spec_key = {'H2': 'H2', 'O2': 'O2', 'N2': 'N2', 'Ar': 'AR'}

        init_temp = 1264.2
        init_pres = 2.18 * ct.one_atm

        gas = ct.Solution(mechanism_filename)

        sim = simulations[0]
        sim.setup_case(mechanism_filename, spec_key)

        assert sim.kind == 'ST'
        np.testing.assert_allclose(sim.time_end, 2.9157e-3)
        np.testing.assert_allclose(sim.gas.T, init_temp)
        np.testing.assert_allclose(sim.gas.P, init_pres)
        mass_fracs = np.zeros(sim.gas.n_species)
        mass_fracs[sim.gas.species_index(spec_key['H2'])] = 0.00444
        mass_fracs[sim.gas.species_index(spec_key['O2'])] = 0.00566
        mass_fracs[sim.gas.species_index(spec_key['Ar'])] = 0.9899
        np.testing.assert_allclose(sim.gas.X, mass_fracs)
        assert sim.n_vars == gas.n_species + 3

        # Check constructed velocity profile
        [times, volumes] = simulation.create_volume_history(
                                mechanism_filename, init_temp, init_pres,
                                'H2:0.00444,O2:0.00566,AR:0.9899',
                                0.10 * 1000., sim.time_end
                                )
        volumes = volumes / volumes[0]
        dVdt = simulation.first_derivative(times, volumes)
        velocities = np.zeros(times.size)
        for i, time in enumerate(times):
            velocities[i] = sim.reac.walls[0].vdot(time)
        np.testing.assert_allclose(dVdt, velocities)

    def test_rcm_setup_case(self):
        """Test that RCM case is set up properly.
        """
        file_path = os.path.join('testfile_rcm.xml')
        filename = pkg_resources.resource_filename(__name__, file_path)
        properties = parse_files.read_experiment(filename)

        # Now create list of Simulation objects
        simulations = parse_files.create_simulations(properties)

        assert len(simulations) == 1

        mechanism_filename = 'gri30.xml'
        spec_key = {'H2': 'H2', 'O2': 'O2', 'N2': 'N2', 'Ar': 'AR'}

        gas = ct.Solution(mechanism_filename)

        sim = simulations[0]
        sim.setup_case(mechanism_filename, spec_key)

        assert sim.kind == 'RCM'
        np.testing.assert_allclose(sim.time_end, 0.01)
        np.testing.assert_allclose(sim.gas.T, 297.4)
        np.testing.assert_allclose(sim.gas.P, 127722.8592)
        mass_fracs = np.zeros(sim.gas.n_species)
        mass_fracs[sim.gas.species_index(spec_key['H2'])] = 0.12500
        mass_fracs[sim.gas.species_index(spec_key['O2'])] = 0.06250
        mass_fracs[sim.gas.species_index(spec_key['N2'])] = 0.18125
        mass_fracs[sim.gas.species_index(spec_key['Ar'])] = 0.63125
        np.testing.assert_allclose(sim.gas.X, mass_fracs)

        times = np.arange(0, 9.7e-2, 1.e-3)
        volumes = np.array([
            5.47669375000E+002, 5.46608789894E+002, 5.43427034574E+002,
            5.38124109043E+002, 5.30700013298E+002, 5.21154747340E+002,
            5.09488311170E+002, 4.95700704787E+002, 4.79791928191E+002,
            4.61761981383E+002, 4.41610864362E+002, 4.20399162234E+002,
            3.99187460106E+002, 3.77975757979E+002, 3.56764055851E+002,
            3.35552353723E+002, 3.14340651596E+002, 2.93128949468E+002,
            2.71917247340E+002, 2.50705545213E+002, 2.29493843085E+002,
            2.08282140957E+002, 1.87070438830E+002, 1.65858736702E+002,
            1.44647034574E+002, 1.23435332447E+002, 1.02223630319E+002,
            8.10119281915E+001, 6.33355097518E+001, 5.27296586879E+001,
            4.91943750000E+001, 4.97137623933E+001, 5.02063762048E+001,
            5.06454851923E+001, 5.10218564529E+001, 5.13374097598E+001,
            5.16004693977E+001, 5.18223244382E+001, 5.20148449242E+001,
            5.21889350372E+001, 5.23536351113E+001, 5.25157124459E+001,
            5.26796063730E+001, 5.28476160610E+001, 5.30202402028E+001,
            5.31965961563E+001, 5.33748623839E+001, 5.35527022996E+001,
            5.37276399831E+001, 5.38973687732E+001, 5.40599826225E+001,
            5.42141273988E+001, 5.43590751578E+001, 5.44947289126E+001,
            5.46215686913E+001, 5.47405518236E+001, 5.48529815402E+001,
            5.49603582190E+001, 5.50642270863E+001, 5.51660349836E+001,
            5.52670070646E+001, 5.53680520985E+001, 5.54697025392E+001,
            5.55720927915E+001, 5.56749762728E+001, 5.57777790517E+001,
            5.58796851466E+001, 5.59797461155E+001, 5.60770054561E+001,
            5.61706266985E+001, 5.62600130036E+001, 5.63449057053E+001,
            5.64254496625E+001, 5.65022146282E+001, 5.65761642150E+001,
            5.66485675508E+001, 5.67208534842E+001, 5.67944133373E+001,
            5.68703658198E+001, 5.69493069272E+001, 5.70310785669E+001,
            5.71146023893E+001, 5.71978399741E+001, 5.72779572372E+001,
            5.73517897984E+001, 5.74167271960E+001, 5.74721573687E+001,
            5.75216388520E+001, 5.75759967785E+001, 5.76575701358E+001,
            5.78058719368E+001, 5.80849611077E+001, 5.85928651155E+001,
            5.94734357453E+001, 6.09310671165E+001, 6.32487551103E+001,
            6.68100309742E+001
            ])
        volumes = volumes / volumes[0]
        dVdt = simulation.first_derivative(times, volumes)
        velocities = np.zeros(times.size)
        for i, time in enumerate(times):
            velocities[i] = sim.reac.walls[0].vdot(time)
        np.testing.assert_allclose(dVdt, velocities)
        assert sim.n_vars == gas.n_species + 3