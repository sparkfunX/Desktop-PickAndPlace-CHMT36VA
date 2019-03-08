# This takes a KiCad POS file and converts it to a CharmHigh desktop pick and place work file 
# Usage: python convert.py MyBoard.POS
# We need to give this script the position file
# Script pulls in feeder data info from a google spreadsheet
# Script outputs to a static file in the directory where the Pick/Place program can read it
# Written by Nathan at SparkFun

# Usage: python convert.py [file name to convert.pos] [directory that contains credentials.txt with trailing\]
# Output will be a workFile.dpv that needs to be copy/pasted into CHJD_SMT\Files directory

import datetime
import sys
import re

import io
import os
import argparse


# Used for pulling data from g spreadsheet
import csv 
import urllib.request, urllib.error, urllib.parse

from Feeder import Feeder
from PartPlacement import PartPlacement
from FileOperations import FileOperations

available_feeders = [] # List of available feeders from user's CSV
components = [] # List of components to be placed from kicad .pos

# The ID from a 'Anyone with the link can view' shared level spreadsheet
# This spreadsheet contains configurations for each different reel of components
#spreadsheet_key = '1PYF-mgUX6ZCsCE1asVujuJHx-Mq8295c7aTCwVem-NQ' # - this is the public key published in the tutorial
spreadsheet_key = '1Lmt0ByYfcVgxzi3jb7mmk2JwgMhg5cnIfpZxwTjLkr4' # - this is the public key for I2BPnP

#Go see if we have secret credentials
# if len(sys.argv) > 2:
#     my_file = sys.argv[2] + "credentials.txt"
#     if os.path.isfile(my_file):
#         # file exists
#         f = open(my_file, "r")
#         spreadsheet_key = f.readline()
#         f.close()
#         print("Using I2B feeder data")
#     else:
#         print("")
#         print(("Could not locate credential file at location: " + my_file))
#         print("")


# This jogs all the components in a direction
# Helpful if we need to adjust the entire job just a smidge
global_x_adjust = 0.0
global_y_adjust = 0


# Convert string to float, default to 0.0
def stof(s, default=0.0):
    try:
        return float(s)
    except ValueError:
        return default

# Convert string to integer, default 0
def stoi(s, default=0):
    try:
        return int(s)
    except ValueError:
        return default

def locate_feeder_info(component_ID):
    # Given a component ID, try to find its name in the available feeders
    # Search the feeder list of aliases as well
    # Returns the ID of the feeder
    
    assert (component_ID < len(components))

    component_name = components[component_ID].component_name()

    for i in range(len(available_feeders)):
        if component_name == available_feeders[i].device_name:
            return available_feeders[i].feeder_ID
        
        if component_name in available_feeders[i].aliases:
            return available_feeders[i].feeder_ID
        

    # If it's not in the feeders look to see if it's a non-mountable device
    # Get the aliases then split them
    nonmount_devices = available_feeders[len(available_feeders)-1].aliases.split(':')
    
    for i in range(len(nonmount_devices)):
        if nonmount_devices[i] in component_name:
            return "NoMount"
        
    #If we still can't find it mark it as a new feeder but with skip/don't mount
    return "NewSkip"

def get_working_name(component_ID):
    # Given a comp ID, return the easy to read name that will be displayed in the software
    # Resolves part to any aliases that may exist
    feeder_ID = locate_feeder_info(component_ID)
    
    if feeder_ID == "NoMount": return feeder_ID
    if feeder_ID == "NewSkip": return feeder_ID
    
    for i in range(len(available_feeders)):
        if feeder_ID == available_feeders[i].feeder_ID:
            return available_feeders[i].device_name

def load_feeder_info_from_net():

    print("Pulling feeder data from the net...")

    # This is the public spreadsheet that contains all our feeder data
    # I'm too tired to use OAuth at the moment
    url = 'https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet=Sheet1'.format(spreadsheet_key)
    print('Fetching feeder data from: {}'.format(url))
    url_data = urllib.request.urlopen(url).read().decode('utf-8')
    response = io.StringIO(url_data)
    fp = csv.reader(response, delimiter=',')

    for row in fp:
        if(row[0] != "Stop"):
            # Add a new feeder using these values
            available_feeders.append(Feeder(feeder_ID=row[1], 
                device_name=row[2], 
                stack_x_offset=stof(row[3]),
                stack_y_offset=stof(row[4]),
                height=stof(row[5]),
                speed=stoi(row[6]),
                head=stoi(row[7]),
                angle_compensation=stoi(row[8]),
                feed_spacing=stoi(row[9]),
                place_component=row[10],
                check_vacuum=row[11],
                use_vision=row[12],
                centroid_correction_x=stof(row[13]),
                centroid_correction_y=stof(row[14]),
                aliases=row[15]
                ))
        else:
            break # We don't want to read in values after STOP

    print("Feeder update complete")


def load_feeder_info_from_file(path):
    # Read from local file
    print('Fetching feeder data from: {}'.format(path))
    with open(path) as fp:
        csvreader = csv.reader(fp)
        next(csvreader, None)  # skip header
        for row in csvreader:
            if(row[0] != "Stop"):
                # Add a new feeder using these values
                available_feeders.append(Feeder(feeder_ID=row[1], 
                    device_name=row[2], 
                    stack_x_offset=stof(row[3]),
                    stack_y_offset=stof(row[4]),
                    height=stof(row[5]),
                    speed=stoi(row[6]),
                    head=stoi(row[7]),
                    angle_compensation=stoi(row[8]),
                    feed_spacing=stoi(row[9]),
                    place_component=row[10],
                    check_vacuum=row[11],
                    use_vision=row[12],
                    centroid_correction_x=stof(row[13]),
                    centroid_correction_y=stof(row[14]),
                    aliases=row[15]
                    ))
            else:
                break # We don't want to read in values after STOP

    print("Feeder update complete")

def load_component_info(component_position_file, mirror_x, board_width):

    # Get position info from file
    componentCount = 0
    with open(component_position_file) as fp:  
        line = fp.readline()
        
        while line:
            if(line[0] != '#'):
                line = re.sub(' +',' ',line) #Remove extra spaces
                token = line.split(' ')
                
                # Add a new component using these values
                components.append(PartPlacement(componentCount, 
                    designator=token[0], 
                    value=token[1], 
                    footprint=token[2], 
                    x=stof(token[3]), 
                    y=stof(token[4]), 
                    rotation=stof(token[5])
                    ))
                
                #componentName = components[componentCount].component_name()

                # Find this component in the available feeders if possible
                components[componentCount].feeder_ID = locate_feeder_info(componentCount)
                
                centroid_correction_x = 0.0
                centroid_correction_y = 0.0
                angle_compensation = 0.0
                head = 0
                    
                # Find this feeder
                if(components[componentCount].feeder_ID != "NoMount" and components[componentCount].feeder_ID != "NewSkip"):
                    for i in range(len(available_feeders)):
                        if(available_feeders[i].feeder_ID == components[componentCount].feeder_ID):
                            centroid_correction_x = available_feeders[i].centroid_correction_x
                            centroid_correction_y = available_feeders[i].centroid_correction_y
                            angle_compensation = available_feeders[i].angle_compensation
                            head = available_feeders[i].head
                            break

                # Correct tape orientation (mounted 90 degrees from the board)
                components[componentCount].rotation = components[componentCount].rotation - 90

                # Add an angle compensation to this component (feeder by feeder)
                components[componentCount].rotation = components[componentCount].rotation + angle_compensation

                # Correct rotations to between -180 and 180
                if(components[componentCount].rotation < -180):
                    components[componentCount].rotation = components[componentCount].rotation + 360
                elif(components[componentCount].rotation > 180):
                    components[componentCount].rotation = components[componentCount].rotation - 360
                    
                # Mirror rotation if needed
                if(mirror_x):
                    components[componentCount].rotation = -components[componentCount].rotation

                # There are some components that have a centroid point in the wrong place (Qwiic Connector)
                # If this component has a correction, use it
                if(components[componentCount].rotation == -180.0):
                    components[componentCount].x = components[componentCount].x + centroid_correction_y
                    components[componentCount].y = components[componentCount].y + centroid_correction_x
                elif(components[componentCount].rotation == 180.0): # Duplicate of first
                    components[componentCount].x = components[componentCount].x + centroid_correction_y
                    components[componentCount].y = components[componentCount].y + centroid_correction_x
                elif(components[componentCount].rotation == -90.0):
                    components[componentCount].y = components[componentCount].y + centroid_correction_y
                    components[componentCount].x = components[componentCount].x + centroid_correction_x
                elif(components[componentCount].rotation == 0.0):
                    components[componentCount].x = components[componentCount].x - centroid_correction_y
                    components[componentCount].y = components[componentCount].y - centroid_correction_x
                elif(components[componentCount].rotation == 90.0):
                    components[componentCount].y = components[componentCount].y - centroid_correction_y
                    components[componentCount].x = components[componentCount].x - centroid_correction_x

                # Assign pick head
                components[componentCount].head = head

                # Add any global corrections
                components[componentCount].y = components[componentCount].y - global_y_adjust
                components[componentCount].x = components[componentCount].x - global_x_adjust
                
                # Add the board width if the file should be mirrored along x
                if (mirror_x):
                    components[componentCount].x = components[componentCount].x + board_width
                
                componentCount = componentCount + 1
            line = fp.readline() # Get the next line
    fp.close()

def add_header(f, outfile, component_position_file):
    d = datetime.datetime.now()

    f.write("separated\n")
    f.write("FILE,{}\n".format(outfile))
    f.write("PCBFILE,{}\n".format(component_position_file))
    f.write("DATE,{:02d}/{:02d}/{:02d}\n".format(d.year, d.month, d.day))
    f.write("TIME,{:02d}:{:02d}:{:02d}\n".format(d.hour, d.minute, d.second))
    f.write("PANELYPE,0\n")

def add_feeders(f):
    # Output used feeders
    f.write("\n")
    f.write("Table,No.,ID,DeltX,DeltY,FeedRates,Note,Height,Speed,Status,SizeX,SizeY,HeightTake,DelayTake\n")
    f.write("\n")
    
    station_number = 0
    for i in range(len(available_feeders)):
        if available_feeders[i].count_in_design != 0:
            
            mount_value = 6
            if available_feeders[i].place_component == False:
                mount_value = 7
                
            # Mount value explanation:
            # 0b.0000.0ABC
            # A = 1 = Use Vision
            # A = 0 = No Vision
            # B = 1 = Use Vacuum Detection
            # B = 0 = No Vacuum Detection
            # C = 1 = Skip placement
            # C = 0 = Place this component
            # Example: 3 = no place, vac, no vis

            f.write('Station,{},{},{:.8g},{:.8g},{},{},{:.8g},{},{},{:.8g},{:.8g},{},{}\n'.format(
                station_number, 
                available_feeders[i].feeder_ID,
                available_feeders[i].stack_x_offset,
                available_feeders[i].stack_y_offset,
                available_feeders[i].feed_spacing,
                available_feeders[i].device_name,
                available_feeders[i].height,
                available_feeders[i].speed,
                mount_value,    # Status
                available_feeders[i].component_size_x,
                available_feeders[i].component_size_y,
                0,  # HeightTake
                0,  # DelayTake
                ))

            station_number = station_number + 1

def add_batch(f):
    # Batch is where the user takes multiple copies of the same design and mounts them
    # into the machine at the same time.
    # Doing an array is where you have one PCB but X number of copies panelized into an array
    
    # If you are doing a batch then the header is
    # PANELYPE,0
    # If you are doing an array then the header is
    # PANELYPE,1
    # Typo is correct.

    # When there is a batch of boards it looks like this
    f.write("\n")
    f.write("Table,No.,ID,DeltX,DeltY\n")
    f.write("\n")
    f.write("Panel_Coord,0,1,0,0\n")

    # When you define an array you get this:
    # Table,No.,ID,IntervalX,IntervalY,NumX,NumY
    #  IntervalX = x spacing. Not sure if this is distance between array
    #  NumX = number of copies in X direction
    # Panel_Array,0,1,0,0,2,2

    # If you have an X'd out PCB in the array you can add a skip record.
    # When you add a skip, you get another
    # Panel_Array,1,4,0,0,2,2 # Skip board #4 in the array
    # This doesn't quite make sense but skips will most likely NOT be automated (user will input an X'd out board during job run)

def add_components(f):
    # Example output
    # Table,No.,ID,PHead,STNo.,DeltX,DeltY,Angle,Height,Skip,Speed,Explain,Note
    # EComponent,0,1,1,1,16.51,12.68,0,0.5,6,0,C4, 0.1uF

    f.write("\n")
    f.write("\n")
    f.write("\n")
    f.write("Table,No.,ID,PHead,STNo.,DeltX,DeltY,Angle,Height,Skip,Speed,Explain,Note,Delay\n")
    f.write("\n")

    record_ID = 1
    record_number = 0
    
    for i in range(len(components)):
        if components[i].feeder_ID in ["NoMount", "NewSkip"]:
            components[i].place_component = False

            
        working_name = get_working_name(components[i].component_ID)
        
        mount_value = 6 # Place record
        if components[i].place_component == False: 
            mount_value = 7 #Skip this record

        f.write('EComponent,{},{},{},{},{:.8g},{:.8g},{:.4g},{:.8g},{},{},{},{},{}\n'.format(
            record_number, 
            record_ID,
            components[i].head,
            components[i].feeder_ID,
            float(components[i].x),
            float(components[i].y),
            float(components[i].rotation),
            float(components[i].height),
            mount_value,
            0,
            components[i].designator,
            working_name,
            0   # Delay
            ))
        
        record_number += 1
        record_ID += 1

def add_ic_tray(f):
    # Add any IC tray info
    f.write("\n")
    f.write("Table,No.,ID,CenterX,CenterY,IntervalX,IntervalY,NumX,NumY,Start\n")
    f.write("\n")

def add_PCB_calibrate(f):
    # Flags to say what type and if calibration of the board has been done
    f.write("\n")
    f.write("Table,No.,nType,nAlg,nFinished\n")
    f.write("\n")
    f.write("PcbCalib,0,1,0,0\n")

    # nType: 0 = use components as calibration marks, 1 = use marks as calibration marks
    # nFinished: ? 0 = you haven't cal'd a board, 1 = you have cal'd the board

def add_fiducials(f):
    # Adds the fiducials or mark information about this board or panel
    # TODO - Should we pull in the marks from the PCB file? It might make better
    # sense to have user do this manually as it will be pretty specific.
    f.write("\n")
    f.write("Table,No.,ID,offsetX,offsetY,Note\n")
    f.write("\n")
    f.write("CalibPoint,0,0,20.1,76,Mark1\n")
    f.write("CalibPoint,1,0,53,1.27,Mark2\n")

def add_calibration_factor(f):
    # Add the calibration factor. This is all the offsets calculated when the
    # PCB is calibrated. We don't have to set anything here because the program
    # will calculate things after user calibrates the PCB.
    
    f.write("\n")
    f.write("Table,No.,DeltX,DeltY,AlphaX,AlphaY,BetaX,BetaY,DeltaAngle\n")
    f.write("\n")
    f.write("CalibFator,0,0,0,0,0,1,1,0\n") # Typo is required

def main(component_position_file, feeder_config_file, outfile=None, mirror_x=False, board_width=0):
    # basic file verification
    for f in [component_position_file, feeder_config_file]:
        if not os.path.isfile(f):
            print ("ERROR: {} is not an existing file".format(f))
            sys.exit(-1)
    


    outfile = "workFile.dpv" if outfile is None else outfile

    # Load all known feeders from file
    load_feeder_info_from_file(feeder_config_file)
        
    # Get position info from file
    load_component_info(component_position_file, mirror_x, board_width)
    
    # Mark all the available feeders that have a component in this design
    for i in range(len(components)):
        for j in range(len(available_feeders)):
            if available_feeders[j].feeder_ID == components[i].feeder_ID:
                available_feeders[j].count_in_design += 1

    print("\nComponents to mount:")
    for comp in [c for c in components if c.feeder_ID not in ['NoMount', 'NewSkip']]:
        print (comp)


    print("\nComponents Not Mounted:")
    for comp in [c for c in components if c.feeder_ID in ['NoMount', 'NewSkip']]:
        print (comp)
        

        
    print("\nUsed Feeders:")
    for i in range(len(available_feeders)):
        if available_feeders[i].count_in_design != 0:
            print(available_feeders[i])
    
    # Output to machine recipe file
    with open(outfile, 'w', newline='\r\n') as f:
        add_header(f, outfile, component_position_file)

        add_feeders(f)
        
        add_batch(f)
        
        add_components(f)
        
        add_ic_tray(f)
        
        add_PCB_calibrate(f)
        
        add_fiducials(f)
        
        add_calibration_factor(f)

    print('Wrote output to {}\n'.format(outfile))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process pos files from KiCAD to this nice, CharmHigh software')
    parser.add_argument('component_position_file', type=str, help='KiCAD position file in ASCII')
    parser.add_argument('feeder_config_file', type=str, help='Feeder CSV file')
    
    parser.add_argument('--output', type=str, help='Output file')
    
    parser.add_argument('--mirror_x', action="store_true", help='Mirror components along X axis. Useful when processing a file with components mounted on the bottom.')
    
    parser.add_argument('--board_width', type=float, help='Board width in mm. Use in conjunction with --mirror-x to make sure the components are aligned to the bottom left side.')

    args = parser.parse_args()

    main(args.component_position_file, args.feeder_config_file, args.output, args.mirror_x, args.board_width)
