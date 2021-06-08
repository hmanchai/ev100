import os
import glob
import shutil
import pandas as pd
import logging
import time
from datetime import timedelta
import fnmatch
import re
import collections




def excel_to_df(excel_pinout):
    df_channels = pd.read_excel(excel_pinout, skiprows = 1, sheet_name=2)
    df_pins = pd.read_excel(excel_pinout, sheet_name=1)
    return df_channels, df_pins

def create_mvp_file(excel_pinout, dest, pin_type_order):
    df_channels, df_pins = excel_to_df(excel_pinout)
    txt_file = open(dest, "w")
    txt_file.write("1 Site(s)\n")
    txt_file.close()
    txt_file = open(dest, "a")
    # add header columns and space after
    column_headers = pd.DataFrame(columns=['MVP       ', 'Pin Name', 'Chassis', 'Slot', 'Channel', 'Site', 'Pattern#', 'Instrument Type'])
    column_headers.to_csv(dest, index=None, sep='\t', mode='a')
    txt_file.write("\n")
    txt_file.close()
    txt_file = open(dest, "a")
    channel_df = pd.DataFrame(columns=['MVP       ', 'Pin Name', 'Chassis', 'Slot', 'Channel', 'Site', 'Pattern#', 'Instrument Type'])
    # add channels
    all_pins_df = pd.DataFrame(columns=['MVP       ', 'Pin Name'])
    channel_df, all_pins_df = add_channel_rows(df_channels, channel_df, '', all_pins_df)
    channel_df, all_pins_df = add_channel_rows(df_channels, channel_df, '.1', all_pins_df)
    channel_df, all_pins_df = add_channel_rows(df_channels, channel_df, '.2', all_pins_df)
    # add all pins, scan in, scan out, clk, jtag, control
    frames = [channel_df, all_pins_df]
    mvp_df = pd.concat(frames)
    mvp_df = add_pin_groups(df_pins, mvp_df, pin_type_order)
    #txt_file.write(channel_df.to_string)

    pd.set_option('display.max_rows', None)
    print(mvp_df)
    mvp_df.to_csv(dest, index=None, sep='\t', header=False, mode='a')
    txt_file.close()

    #convert txt to mvp
    base = os.path.splitext(dest)[0]
    mvp_filepath = base + '.MVP'
    if os.path.exists(mvp_filepath):
        os.remove(mvp_filepath)
    os.rename(dest, base + '.MVP')
    print("Successfully generate MVP file")

def add_pin_groups(df_pins, mvp_df, pin_type_order):
    for pin_type in pin_type_order:
        gpio_column = df_pins.columns.get_loc(pin_type)
        type_column = gpio_column + 1
        sub_df = df_pins.iloc[1:,gpio_column: type_column+1]
        sub_df = sub_df.dropna(how='all')
        sub_df.set_axis(['Pin Name', 'MVP       '], axis='columns', inplace=True)
        sub_df = sub_df[['MVP       ', 'Pin Name']]
        sub_df['MVP       '] = sub_df['MVP       '].apply(lambda x: pin_type_order.get(pin_type))
        sub_df['MVP       '] = sub_df['MVP       '].apply(lambda x: "{:<15}".format(x))
        sub_df['Pin Name'] = sub_df['Pin Name'].apply(lambda x: x.lower())
        sub_df['Pin Name'] = sub_df['Pin Name'].apply(lambda x: "{:<15}".format(x))
        frames = [mvp_df, sub_df]
        mvp_df = pd.concat(frames)
    return mvp_df


def add_channel_rows(df_channels, mvp_df, column_num, all_pins_df):
    for i, row in df_channels.iterrows():
        if not pd.isnull(row['HD Pins' + column_num]):
            gpio_regex = "(GPIO)(\()(.*)(\))"
            ev_100_regex = "(EV100_)(.*)"
            mvp_df, all_pins_df = get_channel_name(column_num, mvp_df, row, gpio_regex, all_pins_df)
            mvp_df, all_pins_df = get_channel_name(column_num, mvp_df, row, ev_100_regex, all_pins_df)
        else:
            break
    return mvp_df, all_pins_df


def get_channel_name(column_num, mvp_df, row, regex, all_pins_df):
    if re.search(regex, row['Channels (Signals)' + column_num]):
        if "(GPIO)(\()(.*)(\))" in regex:
            pin = re.search(regex, row['Channels (Signals)' + column_num]).group(3)
            pin_name = 'gpio_' + pin
        else:
            pin = re.search(regex, row['Channels (Signals)' + column_num]).group(2)
            pin_name = pin.lower()
        channel_num = int(row['Channel(DD192)' + column_num])
        pin_name = "{:<15}".format(pin_name)
        new_row = {'MVP       ': pin_name, 'Pin Name': pin_name, 'Chassis': 'A', 'Slot': '2', 'Channel': channel_num,
                   'Site': '1', 'Pattern#': '1', 'Instrument Type': '        Digital'}
        mvp_df = mvp_df.append(new_row, ignore_index=True)
        all_pins = 'ALL_PINS'
        all_pins = "{:<15}".format(all_pins)
        all_pins_row = {'MVP       ': all_pins, 'Pin Name': pin_name}
        all_pins_df = all_pins_df.append(all_pins_row, ignore_index=True)
    return mvp_df, all_pins_df



def main():
    chip_version = 'Waipio'
    #dest = r"C:\AxiTestPrograms\Qualcomm" + "\\'" + chip_version + r"\Common\QCOM_" + chip_version + r"_WY_v2.MVP"
    dest = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\MVP file generation\QCOM_Waipio_WY_v2.txt"
    excel_pinout = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Documents\waipio_cdp_pinout_v1.2.xlsx"
    pin_type_order = collections.OrderedDict()
    pin_type_order = {'Scan In': 'IN', 'Scan Out': 'OUT', 'Clocks': 'CLK', 'JTAG': 'JTAG',
                      'EV-100 Control/Sel': 'CONTROL'}
    create_mvp_file(excel_pinout, dest, pin_type_order)

if __name__ == "__main__":
    main()