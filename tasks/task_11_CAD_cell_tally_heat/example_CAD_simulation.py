#!/usr/bin/env python3

"""example_CAD_simulation.py: uses a dagmc.h5m file for the geometry."""

__author__ = "Jonathan Shimwell"

import openmc
import json
import os
from neutronics_material_maker import Material
from parametric_plasma_source import Plasma

# MATERIALS using the neutronics material maker

breeder_material = Material(material_name='Li4SiO4', enrichment=90).openmc_material

copper = Material(material_name="copper").openmc_material

eurofer = Material(material_name='eurofer').openmc_material

mats = openmc.Materials([breeder_material, eurofer, copper])


# GEOMETRY using dagmc doesn't contain any CSG geometry

universe = openmc.Universe()
geom = openmc.Geometry(universe)


# SIMULATION SETTINGS

# Instantiate a Settings object
sett = openmc.Settings()
batches = 10
sett.batches = batches
sett.inactive = 0
sett.particles = 1000
sett.run_mode = 'fixed source'
sett.dagmc = True  # this is the openmc command enables use of the dagmc.h5m file as the geometry


# creates a source object
source = openmc.Source()
# this creates a neutron distribution with the shape of a tokamak plasma
my_plasma = Plasma(elongation=2.9,
                   minor_radius=1.118,
                   major_radius=1.9,
                   triangularity = 0.55)
# there are other parameters that can be set for the plasma, but we can use the defaults for now
my_plasma.export_plasma_source('my_custom_plasma_source.so')
# sets the source poition, direction and energy with predefined plasma parameters (see source_sampling.cpp)
source.library = './my_custom_plasma_source.so'
sett.source = source


tallies = openmc.Tallies()

tbr_tally = openmc.Tally(name='TBR')
tbr_tally.scores = ['(n,Xt)']  # MT 205 is the (n,Xt) reaction where X is a wildcard, if MT 105 or (n,t) then some tritium production will be missed, for example (n,nt) which happens in Li7 would be missed
tallies.append(tbr_tally)


# Run OpenMC!
model = openmc.model.Model(geom, mats, sett, tallies)
sp_filename = model.run()

# open the results file
sp = openmc.StatePoint(sp_filename)

# access the tally
tbr_tally = sp.get_tally(name='TBR')
df = tbr_tally.get_pandas_dataframe()
tbr_tally_result = df['mean'].sum()

# print result
print('The tritium breeding ratio was found, TBR = ', tbr_tally_result)

# output result in json file
json_output = {'TBR': tbr_tally_result}
with open('cad_simulation_results.json', 'w') as file_object:
    json.dump(json_output, file_object, indent=2)
os.system('cp cad_simulation_results.json /my_openmc_workshop')
