#!/usr/bin/env python
# coding: utf-8

# In[54]:


import re
import string
from opentrons import protocol_api ,simulate
from opentrons import types
import opentrons.execute


############# SET UP OPENTRONS API AND LABWARE ################
protocol = opentrons.execute.get_protocol_api('2.3')
protocol.home()

nrows = 24
ncols = 24
reservoir = protocol.load_labware('nest_12_reservoir_15ml' ,1)
square_wells = protocol.load_labware('nest_96_wellplate_2ml_deep' ,2)
tiprack_1 = protocol.load_labware('opentrons_96_tiprack_20ul' ,3)
tiprack_2 = protocol.load_labware('opentrons_96_tiprack_20ul' ,4)
tiprack_3 = protocol.load_labware('opentrons_96_tiprack_20ul' ,5)
tiprack_4 = protocol.load_labware('opentrons_96_tiprack_20ul' ,6)
multi_channel = protocol.load_instrument('p20_multi_gen2' ,'left' ,
                                             tip_racks=[tiprack_1 ,tiprack_2 ,tiprack_3 ,tiprack_4])
single_channel = protocol.load_instrument('p20_single_gen2' ,'right' ,
                                              tip_racks=[tiprack_1 ,tiprack_2 ,tiprack_3 ,tiprack_4])
reservoir_dic = {'red': reservoir['A1'] ,'green': reservoir['A2'] ,'yellow': reservoir['A3'] ,'brown': reservoir['A4']}

###### DECODE GUI GRID DATA ######

def neat_grid_info(txt_file):
    '''Takes input from GUI Grid and cleans it up
       Returns nested list: [[color1], [wells of color1]
                             [color2], [wells of color2]...]'''
    with open(txt_file ,'r') as f:


        # cutting from 24x24 to 16x24
        letter_cols = list(string.ascii_uppercase[:24])
        number_rows = [x for x in range(1,9)]
        igonred_squares = [i+str(j) for i in letter_cols for j in number_rows]

        sample_text = f.read()
        sample_text = sample_text.split("\n")
        ignore_lines = ['----' ,'---' ,'-----' ,'------' ,'']  # any content you want to delete
        neat = [y for y in sample_text if y not in ignore_lines]  # removes the lines you want deleted

        #print(neat)
        neat2 = []
        for ele in neat:
            lis = ele.split(',')
            for i, square in enumerate(lis):
                lis[i] = square.replace(' ', '')

            if has_numbers(lis[0]):
                lis = [square for square in lis if square not in igonred_squares]

            neat2.append(lis)
            

        neater = []
        for lis in neat2:
            if len(lis) > 0:
                if has_numbers(lis[0])and has_numbers(neater[-1][0]):
                    for i in lis:
                        neater[-1].append(i)
                else:
                    neater.append(lis)

        return neater


def has_numbers(s):
    ''''Checks if any number in string'''
    return any(char.isdigit() for char in s)


def string_to_grid_coor(s ,nrows):
    '''Takes string of squares 'A1, B5, C6, D8'
       Returns the coor in a nrows x ncols grid
       such that top-left square in Grid() is (0,0)
       and bottom-right is (nrows, ncols)'''
    res = re.split('(\d+)' ,s)[:-1]
    coor = ['_' ,0]
    for item in res:
        if item.isalpha():
            col = ord(item.lower()) - 97
            coor[1] = col

        if item.isnumeric():
            row = nrows - int(item)
            coor[0] = row

    return (coor)

def decodifier(neat_grid):
    '''Takes all neat_grid_info() data
        calls string_to_coor() for each element in
        [squares with color1], [squares with color2], ...
        converts the squares to coor system  '''

    adapted_coor_dic = {}

    for i in range(0 ,len(neat_grid), 2):
        color = neat_grid[i][0]
        squares_with_color = neat_grid[i + 1]
        adapted_grid_coor = []

        for square in squares_with_color:
            square_no_space = square.replace(' ' ,'')

            adapted_square_coor = string_to_grid_coor(square_no_space ,nrows)
            adapted_grid_coor.append(tuple(adapted_square_coor))

        adapted_coor_dic[color] = adapted_grid_coor

    return adapted_coor_dic

def well_finder(tuple_coor):
    '''Takes a coor e.g. (0, 3) or (9, 9)
       converts to a well_ID, e.g. 'A4', 'C12' '''

    # x-axis, row, letter value [A, B, ..., H]
    row = tuple_coor[0]

    x_coor = [(x ,x + 1) for x in range(0 ,16 ,2)]
    for i ,coor in enumerate(x_coor):
        if coor[0] == row or coor[1] == row:
            letter = string.ascii_uppercase[i]

    # y-axis, col, number value [A, B, ..., H]
    col = tuple_coor[1]
    columns = [col for col in range(1 ,25)]

    y_coor = [(x ,x + 1) for x in range(0 ,24 ,2)]
    for i ,coor in enumerate(y_coor):
        if coor[0] == col or coor[1] == col:
            number = columns[i]

    well_ID = letter + str(number)

    return well_ID



def paint(well, abcd, color):
    

    o = square_wells[well].center()
    l = square_wells[well].length
    w = square_wells[well].width
    if abcd == 'a':
        point = o.move(types.Point(x=-w / 4 ,y=+l / 4 ,z=0))
    elif abcd == 'b':
        point = o.move(types.Point(x=+w / 4 ,y=+l / 4 ,z=0))
    elif abcd == 'c':
        point = o.move(types.Point(x=-w / 4 ,y=-l / 4 ,z=0))
    elif abcd == 'd':
        point = o.move(types.Point(x=+w / 4 ,y=-l / 4 ,z=0))

    single_channel.pick_up_tip()
    single_channel.aspirate(2 ,reservoir_dic[color])
    single_channel.move_to(point)
    single_channel.dispense()
    single_channel.drop_tip()


def run():
    
    ncols = 24
    nrows = 24


    A_loc = [(i ,j) for i in range(0, nrows, 2) for j in range(0, ncols, 2)]
    B_loc = [(i ,j + 1) for i in range(0, nrows, 2) for j in range(0, ncols, 2)]
    C_loc = [(i + 1 ,j) for i in range(0, nrows, 2) for j in range(0, ncols, 2)]
    D_loc = [(i + 1 ,j + 1) for i in range(0, nrows, 2) for j in range(0, ncols, 2)]

    count = 0

    for color ,locations in adapted_coor_dic.items():

        for l in locations:
            count += 1
            print('Count: ' + str(count))
            if l in A_loc:
                well = well_finder(l)
                paint(well ,'a' ,color)
                print('Painted with ' + color + ' at position A in ' + well)
            elif l in B_loc:
                well = well_finder(l)
                paint(well ,'b' ,color)
                print('Painted with ' + color + ' at position B in ' + well)
            elif l in C_loc:
                well = well_finder(l)
                paint(well ,'c' ,color)
                print('Painted with ' + color + ' at position C in ' + well)
            elif l in D_loc:
                well = well_finder(l)
                paint(well ,'d' ,color)
                print('Painted with ' + color + ' at position D in ' + well)


############# CALLING FUNCTIONS ################

neat_grid = neat_grid_info('tree_Marie_Antronette.txt')

adapted_coor_dic = decodifier(neat_grid)

metadata = {'apiLevel': '2.3'}
protocol = opentrons.execute.get_protocol_api('2.3')
protocol.home()

run()

