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
from collections import OrderedDict

import pyexcel

from Feeder import Feeder
from ICTray import ICTray
from PartPlacement import PartPlacement
from FileOperations import FileOperations

available_feeders = [] # List of available feeders from user's CSV
ic_trays = []
components = [] # List of components to be placed from kicad .pos
fiducials = [] # Detected fiducials inside the components list (components designators beginning with FID*)

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

def clear_utf8_characters(str):
    str = str.replace('μ','u')
    str = str.replace('Ω','Ohm')
    return str

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
    if feeder_ID == "NewSkip": return components[component_ID].component_name()

    for i in range(len(available_feeders)):
        if feeder_ID == available_feeders[i].feeder_ID:
            return available_feeders[i].device_name

def get_feeder(feeder_ID):
    # Given the feeder ID, return the associated Feeder object
    for i in range(len(available_feeders)):
        if(available_feeders[i].feeder_ID == feeder_ID):
            return available_feeders[i]
    return Feeder()

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
                device_name=clear_utf8_characters(row[2]),
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
    for row in pyexcel.get_array(file_name=path, start_row=1): # skip header
        if(row[0] != "Stop"):
            # Add a new feeder using these values
            available_feeders.append(Feeder(feeder_ID=row[1],
                device_name=clear_utf8_characters(row[2]),
                stack_x_offset=stof(row[3]),
                stack_y_offset=stof(row[4]),
                height=stof(row[5]),
                speed=stoi(row[6]),
                head=stoi(row[7]),
                angle_compensation=stoi(row[8]),
                feed_spacing=stoi(row[9]),
                place_component=(row[10] == 'Y'),
                check_vacuum=(row[11] == 'Y'),
                use_vision=(row[12] == 'Y'),
                centroid_correction_x=stof(row[13]),
                centroid_correction_y=stof(row[14]),
                aliases=row[15]
                ))
        else:
            break # We don't want to read in values after STOP

    print("Feeder update complete")


def load_cuttape_info_from_file(path):
    # Read from local file
    print('Fetching CutTape data from: {}'.format(path))
    for row in pyexcel.get_array(file_name=path, start_row=1): # skip header
        # print("ID {}, {} columns".format(row[1], len(row)))
        if(row[0] != "Stop"):
        # Append to feeder list
            # Add a new feeder using these values
            available_feeders.append(Feeder(feeder_ID=row[1],
                device_name=clear_utf8_characters(row[2]),
                stack_x_offset=0,
                stack_y_offset=0,
                height=stof(row[7]),
                speed=stoi(row[8]),
                head=stoi(row[9]),
                angle_compensation=stoi(row[10]),
                feed_spacing=0,#stoi(row[9]),
                place_component=(row[11] == 'Y'),
                check_vacuum=(row[12] == 'Y'),
                use_vision=(row[13] == 'Y'),
                centroid_correction_x=stof(row[14]),
                centroid_correction_y=stof(row[15]),
                aliases=row[16] if len(row) > 16 else ""
                ))

        # Append to the IC Tray Data
            ic_trays.append(ICTray(feeder_ID=row[1],
                first_IC_center_X=stof(row[3]),
                first_IC_center_Y=stof(row[4]),

                last_IC_center_X=stof(row[3]) + stoi(row[6]) * (stoi(row[5]) - 1),
                last_IC_center_Y=stof(row[4]),
                number_X=stoi(row[5]),
                number_Y=1,
                start_IC=0
            ))
        else:
            break # We don't want to read in values after STOP

    print("Feeder update complete")

def load_component_info(component_position_file, offset, mirror_x, board_width):
    # Get position info from file
    componentCount = 0
    with open(component_position_file, encoding='utf-8') as fp:
        line = fp.readline()

        while line:
            if(line[0] != '#'):
                line = re.sub(' +',' ',line) #Remove extra spaces
                token = line.split(' ')
                # Add a new component using these values
                components.append(PartPlacement(componentCount,
                    designator=token[0],
                    value=clear_utf8_characters(token[1]),
                    footprint=token[2],
                    x=stof(token[3]),
                    y=stof(token[4]),
                    rotation=stof(token[5])
                    ))

                #componentName = components[componentCount].component_name()

                # Find this component in the available feeders if possible
                components[componentCount].feeder_ID = locate_feeder_info(componentCount)

                # Find the associated feeder
                feeder = get_feeder(components[componentCount].feeder_ID)

                # Correct tape orientation (mounted 90 degrees from the board)
                components[componentCount].rotation = components[componentCount].rotation - 90

                # Add an angle compensation to this component (feeder by feeder)
                components[componentCount].rotation = components[componentCount].rotation + feeder.angle_compensation

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
                    components[componentCount].x = components[componentCount].x + feeder.centroid_correction_y
                    components[componentCount].y = components[componentCount].y + feeder.centroid_correction_x
                elif(components[componentCount].rotation == 180.0): # Duplicate of first
                    components[componentCount].x = components[componentCount].x + feeder.centroid_correction_y
                    components[componentCount].y = components[componentCount].y + feeder.centroid_correction_x
                elif(components[componentCount].rotation == -90.0):
                    components[componentCount].y = components[componentCount].y + feeder.centroid_correction_y
                    components[componentCount].x = components[componentCount].x + feeder.centroid_correction_x
                elif(components[componentCount].rotation == 0.0):
                    components[componentCount].x = components[componentCount].x - feeder.centroid_correction_y
                    components[componentCount].y = components[componentCount].y - feeder.centroid_correction_x
                elif(components[componentCount].rotation == 90.0):
                    components[componentCount].y = components[componentCount].y - feeder.centroid_correction_y
                    components[componentCount].x = components[componentCount].x - feeder.centroid_correction_x

                # Assign pick head, speed and other feeder parameters
                components[componentCount].head = feeder.head
                components[componentCount].place_component = feeder.place_component
                components[componentCount].check_vacuum = feeder.check_vacuum
                components[componentCount].use_vision = feeder.use_vision

                # Add any global corrections (offset)
                components[componentCount].y = components[componentCount].y + offset[1]
                components[componentCount].x = components[componentCount].x + offset[0]

                # Add the board width if the file should be mirrored along x
                if (mirror_x):
                    components[componentCount].x = components[componentCount].x + board_width

                componentCount = componentCount + 1
            line = fp.readline() # Get the next line
    fp.close()

def find_fiducials():
    # Detect all components whose designator begins with FID and add it to the fiducials list
    for c in components:
        if c.designator.startswith('FID'):
            fiducials.append(c)


def add_header(f, outfile, component_position_file):
    d = datetime.datetime.now()

    f.write("separated\n")
    f.write("FILE,{}\n".format(os.path.basename(outfile)))
    f.write("PCBFILE,{}\n".format(os.path.basename(component_position_file)))
    f.write("DATE,{:02d}/{:02d}/{:02d}\n".format(d.year, d.month, d.day))
    f.write("TIME,{:02d}:{:02d}:{:02d}\n".format(d.hour, d.minute, d.second))
    f.write("PANELYPE,0\n")

def add_feeders(f):
    # Output used feeders
    f.write("\n")
    f.write("Table,No.,ID,DeltX,DeltY,FeedRates,Note,Height,Speed,Status,SizeX,SizeY,HeightTake,DelayTake\n")

    station_number = 0
    for i in range(len(available_feeders)):
        if available_feeders[i].count_in_design != 0 and available_feeders[i].feeder_ID != "NoMount":

            # Mount value explanation:
            # 0b.0000.0ABC
            # A = 1 = Use Vision
            # A = 0 = No Vision
            # B = 1 = Use Vacuum Detection
            # B = 0 = No Vacuum Detection
            # C = 1 = Skip placement
            # C = 0 = Place this component
            # Example: 3 = no place, vac, no vis
            mount_value = 0
            if available_feeders[i].place_component == False:
                mount_value += 1
            if available_feeders[i].check_vacuum == True:
                mount_value += 2
            if available_feeders[i].use_vision == True:
                mount_value += 4


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

def add_components(f, include_newskip):
    # Example output
    # Table,No.,ID,PHead,STNo.,DeltX,DeltY,Angle,Height,Skip,Speed,Explain,Note
    # EComponent,0,1,1,1,16.51,12.68,0,0.5,6,0,C4, 0.1uF

    f.write("\n")
    f.write("Table,No.,ID,PHead,STNo.,DeltX,DeltY,Angle,Height,Skip,Speed,Explain,Note,Delay\n")

    record_ID = 1
    record_number = 0

    for i in range(len(components)):
        if components[i].feeder_ID == "NoMount":
            continue # Do not include NoMount components in the DPV file

        if components[i].feeder_ID == "NewSkip":
            if not include_newskip:
                continue # No not include NewSkip components unless explicitly asked
            components[i].place_component = False

        working_name = get_working_name(components[i].component_ID)

        # 0b.0000.0ABC
        # A = 1 = Use Vision
        # A = 0 = No Vision
        # B = 1 = Use Vacuum Detection
        # B = 0 = No Vacuum Detection
        # C = 1 = Skip placement
        # C = 0 = Place this component
        # Example: 3 = no place, vac, no vis
        mount_value = 0
        if components[i].place_component == False:
            mount_value += 1
        if components[i].check_vacuum == True:
            mount_value += 2
        if components[i].use_vision == True:
            mount_value += 4

        f.write('EComponent,{},{},{},{},{:.8g},{:.8g},{:.4g},{:.8g},{},{},{},{},{}\n'.format(
            record_number,
            record_ID,
            components[i].head,
            components[i].feeder_ID if components[i].feeder_ID != "NewSkip" else 99,
            float(components[i].x),
            float(components[i].y),
            float(components[i].rotation),
            float(components[i].height),
            mount_value,
            components[i].speed,
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

    for idx, tray in enumerate(ic_trays):
        f.write("ICTray,{},{},{},{},{},{},{},{},{}\n".format(
            idx,
            tray.feeder_ID,
            tray.first_IC_center_X,
            tray.first_IC_center_Y,
            tray.last_IC_center_X,
            tray.last_IC_center_Y,
            tray.number_X,
            tray.number_Y,
            tray.start_IC
        ))


def add_PCB_calibrate(f):
    # Flags to say what type and if calibration of the board has been done
    f.write("\n")
    f.write("Table,No.,nType,nAlg,nFinished\n")

    # nType: 0 = use components as calibration marks, 1 = use marks as calibration marks
    # nFinished: ? 0 = you haven't cal'd a board, 1 = you have cal'd the board
    calib_type = 0
    if (len(fiducials) >= 2):
        calib_type = 1
        print("\nDetected fiducials:")

    f.write("PcbCalib,0,{},0,0\n".format(calib_type))


def add_fiducials(f):
    # Adds the fiducials or mark information about this board or panel
    # If 2 or more fiducials are detected (designator starts with FID) then they
    # are automatically added. User can still change these later within the CharmHigh
    # software
    # TODO if more than 3 fiducials are detected, select the fiducials to use based on their position (ex: panels)
    f.write("\n")
    f.write("Table,No.,ID,offsetX,offsetY,Note\n")

    if (len(fiducials) >= 2):
        for i in range(min(len(fiducials), 3)):
            f.write("CalibPoint,{},0,{},{},Mark{}\n".format(i, fiducials[i].x, fiducials[i].y, i+1))
            print("{}: \t{}\t{}".format(fiducials[i].designator, fiducials[i].x, fiducials[i].y))


def add_calibration_factor(f):
    # Add the calibration factor. This is all the offsets calculated when the
    # PCB is calibrated. We don't have to set anything here because the program
    # will calculate things after user calibrates the PCB.

    f.write("\n")
    f.write("Table,No.,DeltX,DeltY,AlphaX,AlphaY,BetaX,BetaY,DeltaAngle\n")
    f.write("CalibFator,0,0,0,0,0,1,1,0\n") # Typo is required


def generate_bom(output_file, include_unassigned_components):
    # Generate bom file with feeder_ID info
    # Useful to order components not on the machine
    print ("Building BOM file...")
    make_reference = lambda c: (c.footprint, c.value, c.feeder_ID)
    c_dict = OrderedDict() # "ref": [c, c, ...]

    # group components by value_package
    for c in components:
        ref = make_reference(c)
        if ref not in c_dict:
            c_dict[ref] = []

        c_dict[ref].append(c)


    # build data
    out_array = [ [ "Id", "Designator", "Package", "Designator/Value", "Quantity", "AutoMounted", "Feeder Type"] ]
    index = 0
    for c_ref in c_dict:
        comp_list = c_dict[c_ref]
        if not include_unassigned_components and c_ref[2] == "NoMount":
            print ("Ignoring {} - {}".format(",".join([str(c.designator) for c in comp_list]), c_ref[0]))
            continue
        if c_ref[2] not in ["NewSkip", "NoMount"]:
            auto_mounted = "True"
            feeder_type = "Feeder" if int(c_ref[2]) < 80 else "Cut Tape"
        else:
            auto_mounted = "False"
            feeder_type = ""
        out_array.append([index, ",".join([str(c.designator) for c in comp_list]), c_ref[0], c_ref[1], len(comp_list), auto_mounted, feeder_type])
        
        index += 1

    pyexcel.save_as(array=out_array, dest_file_name=output_file)
    print ("Wrote output at {}".format(output_file))

def main(component_position_file, feeder_config_file, cuttape_config_file, outfile=None, include_newskip=False, offset=[0, 0], mirror_x=False, board_width=0, bom_output_file=None):
    # basic file verification
    for f in [component_position_file, feeder_config_file]:
        if not os.path.isfile(f):
            print ("ERROR: {} is not an existing file".format(f))
            sys.exit(-1)


    if outfile is None:
        basename = os.path.splitext(os.path.basename(component_position_file))[0]

        outfile = os.path.join('output', "{date}-{basename}.dpv".format(date=datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), basename=basename))
        os.makedirs('output', exist_ok=True)

    # Load all known feeders from file
    load_feeder_info_from_file(feeder_config_file)
    if cuttape_config_file is not None:
        load_cuttape_info_from_file(cuttape_config_file)

    # Get position info from file
    load_component_info(component_position_file, offset, mirror_x, board_width)

    # Detect fiducials in the components list
    find_fiducials()

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
        if available_feeders[i].count_in_design != 0 and available_feeders[i].feeder_ID != "NoMount":
            print(available_feeders[i])

    # Output to machine recipe file
    with open(outfile, 'w', encoding='utf-8', newline='\r\n') as f:
        add_header(f, outfile, component_position_file)

        add_feeders(f)

        add_batch(f)

        add_components(f, include_newskip)

        add_ic_tray(f)

        add_PCB_calibrate(f)

        add_fiducials(f)

        add_calibration_factor(f)

    print('\nWrote output to {}\n'.format(outfile))

    if bom_output_file is not None:
        generate_bom(bom_output_file, include_newskip)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process pos files from KiCAD to this nice, CharmHigh software')
    parser.add_argument('component_position_file', type=str, help='KiCAD position file in ASCII')
    parser.add_argument('feeder_config_file', type=str, help='Feeder definition file. Supported file formats : csv, ods, fods, xls, xlsx,...')

    parser.add_argument("--cuttape_config_file", type=str, help='Cut Tape Definition file. Supported file formats : csv, ods, fods, xls, xlsx,...')

    parser.add_argument('--output', type=str, help='Output file. If not specified, the position file name is used and the dpv file is created in the output/ folder.')
    parser.add_argument('--bom-file', type=str, help='Output BOM file. Generate a BOM with feeder info / NotMounted')

    parser.add_argument('--include_unassigned_components', action="store_true", help='Include in the output file the components not associated to any feeder. By default these components will be assigned to feeder 99 and not placed but can still be manually assigned to a custom tray.')

    parser.add_argument('--offset', nargs=2, type=float, default=[0, 0], metavar=('x', 'y'), help='Global offset added to every component.')

    mirror_group = parser.add_argument_group("Processing bottom component files")
    mirror_group.add_argument('--mirror_x', action="store_true", help='Mirror components along X axis. Useful when processing a file with components mounted on the bottom.')

    mirror_group.add_argument('--board_width', type=float, help='Board width in mm. Use in conjunction with --mirror-x to make sure the components are aligned to the bottom left side.')

    args = parser.parse_args()

    main(args.component_position_file, args.feeder_config_file, args.cuttape_config_file, args.output, args.include_unassigned_components, args.offset, args.mirror_x, args.board_width, args.bom_file)
