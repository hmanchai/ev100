import os
import glob
import shutil
import pandas as pd
import numpy as np
import logging
import time
from datetime import timedelta
import fnmatch
import re
import collections
import numbers


class Generate_MVP():
    def __init__(self, excel_pinout, chip_version):
        self.excel_pinout = excel_pinout
        self.chip_version = chip_version
        # dest = r"C:\AxiTestPrograms\Qualcomm" + "\\'" + chip_version + r"\Common\QCOM_" + chip_version + r"_WY_v2.MVP"
        self.dest = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\MVP file generation\QCOM_Waipio_WY_v2.txt"
        self.pin_type_order = collections.OrderedDict()
        self.pin_type_order = {'Scan In': 'IN', 'Scan Out': 'OUT', 'Clocks': 'CLK', 'JTAG': 'JTAG',
                          'EV-100 Control/Sel': 'CONTROL'}
        self.connector_col_order = ['HD Pins', 'Channels (Signals)', 'Channel(DD192)']

    def excel_to_df(self, excel_pinout, connector_col_order):
        df_channels = pd.read_excel(excel_pinout, skiprows = 1, sheet_name=2)
        df_channels.dropna(how='all')
        frames = []
        col_header = []
        for i, col_order in enumerate(connector_col_order):
            col_header.append([col for col in df_channels.columns if col_order in col])

        col_header = np.transpose(col_header)


        for col in col_header:
            temp_df = df_channels[col]
            temp_df.set_axis(col_header[0], axis='columns', inplace=True)
            frames.append(temp_df)

        df_channels = pd.concat(frames)
        df_channels = df_channels.dropna(axis=0, how = 'all')

        df_channels.reset_index(drop=True, inplace=True)

        df_pins = pd.read_excel(excel_pinout, sheet_name=1)
        return df_channels, df_pins

    def create_mvp_file(self):
        df_channels, df_pins = self.excel_to_df(self.excel_pinout, self.connector_col_order)
        txt_file = open(self.dest, "w")
        txt_file.write("1 Site(s)\n")
        txt_file.close()
        txt_file = open(self.dest, "a")
        # add header columns and space after
        column_header_order = ['MVP       ', 'Pin Name', 'Chassis', 'Slot', 'Channel', 'Site', 'Pattern#', 'Instrument Type']
        column_headers = pd.DataFrame(columns=column_header_order)
        column_headers.to_csv(self.dest, index=None, sep='\t', mode='a')
        txt_file.write("\n")
        txt_file.close()
        txt_file = open(self.dest, "a")
        temp_df = pd.DataFrame(columns=column_header_order)
        # add channels
        all_pins_df = pd.DataFrame(columns=['MVP       ', 'Pin Name'])
        temp_df, all_pins_df = self.add_channel_rows(df_channels, temp_df, all_pins_df, self.connector_col_order)

        # add all pins, scan in, scan out, clk, jtag, control
        frames = [temp_df, all_pins_df]
        mvp_df = pd.concat(frames)
        mvp_df = self.add_pin_groups(df_pins, mvp_df, self.pin_type_order)
        #txt_file.write(temp_df.to_string)

        pd.set_option('display.max_rows', None)
        mvp_df.to_csv(self.dest, index=None, sep='\t', header=False, mode='a')
        txt_file.close()

        #convert txt to mvp
        base = os.path.splitext(self.dest)[0]
        mvp_filepath = base + '.MVP'
        if os.path.exists(mvp_filepath):
            os.remove(mvp_filepath)
        os.rename(self.dest, base + '.MVP')
        print("Successfully generate MVP file")

    def add_pin_groups(self, df_pins, mvp_df, pin_type_order):
        mvp_spacing = 'MVP       '
        pin_name = 'Pin Name'
        for pin_type in pin_type_order:
            gpio_column = df_pins.columns.get_loc(pin_type)
            type_column = gpio_column + 1
            sub_df = df_pins.iloc[1:,gpio_column: type_column+1]
            sub_df = sub_df.dropna(how='all')
            sub_df.set_axis([pin_name, mvp_spacing], axis='columns', inplace=True)
            sub_df = sub_df[[mvp_spacing, pin_name]]
            sub_df[mvp_spacing] = sub_df[mvp_spacing].apply(lambda x: pin_type_order.get(pin_type))
            sub_df[mvp_spacing] = sub_df[mvp_spacing].apply(lambda x: "{:<15}".format(x))
            sub_df[pin_name] = sub_df[pin_name].apply(lambda x: x.lower())
            sub_df[pin_name] = sub_df[pin_name].apply(lambda x: self.mode_correction(x))
            sub_df[pin_name] = sub_df[pin_name].apply(lambda x: "{:<15}".format(x))
            frames = [mvp_df, sub_df]
            mvp_df = pd.concat(frames)
        return mvp_df


    def add_channel_rows(self, df_channels, mvp_df,all_pins_df, connector_col_order):
        for i, row in df_channels.iterrows():
            if not pd.isnull(row[connector_col_order[0]]):
                if isinstance(row[connector_col_order[0]], numbers.Number):
                    gpio_regex = "(GPIO)(\()(.*)(\))"
                    ev_100_regex = "(EV100_)(.*)"
                    mvp_df, all_pins_df = self.get_channel_name(mvp_df, row, gpio_regex, all_pins_df, connector_col_order)
                    mvp_df, all_pins_df = self.get_channel_name(mvp_df, row, ev_100_regex, all_pins_df, connector_col_order)
            else:
                continue
        return mvp_df, all_pins_df


    def get_channel_name(self, mvp_df, row, regex, all_pins_df, connector_col_order):
        if re.search(regex, row[connector_col_order[1]]):
            if "(GPIO)(\()(.*)(\))" in regex:
                pin = re.search(regex, row[connector_col_order[1]]).group(3)
                pin_name = 'gpio_' + pin
            else:
                pin = re.search(regex, row[connector_col_order[1]]).group(2)
                pin_name = pin.lower()
                pin_name = self.mode_correction(pin_name)
                pin_name = self.jtag_correction(pin_name)

            channel_num = int(row[connector_col_order[2]])
            pin_name = "{:<15}".format(pin_name)
            new_row = {'MVP       ': pin_name, 'Pin Name': pin_name, 'Chassis': 'A', 'Slot': '2', 'Channel': channel_num,
                       'Site': '1', 'Pattern#': '1', 'Instrument Type': '        Digital'}
            mvp_df = mvp_df.append(new_row, ignore_index=True)
            all_pins = 'ALL_PINS'
            all_pins = "{:<15}".format(all_pins)
            all_pins_row = {'MVP       ': all_pins, 'Pin Name': pin_name}
            all_pins_df = all_pins_df.append(all_pins_row, ignore_index=True)
        return mvp_df, all_pins_df


    def mode_correction(self, pin_name):
        if re.search("(mode)(.*)", pin_name):
            if re.search("(_)", pin_name) == None:
                pin_name = 'mode' + '_' + re.search("(mode)(.*)", pin_name).group(2)
        return pin_name

    def jtag_correction(self, pin_name):
        if re.search("(jtag_)(.*)", pin_name):
            if re.search("(jtag_sel)", pin_name) == None:
                pin_name = re.search("(jtag_)(.*)", pin_name).group(2)
        return pin_name

def main():
    chip_version = 'Waipio'
    # #dest = r"C:\AxiTestPrograms\Qualcomm" + "\\'" + chip_version + r"\Common\QCOM_" + chip_version + r"_WY_v2.MVP"
    # dest = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\MVP file generation\QCOM_Waipio_WY_v2.txt"
    excel_pinout = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Documents\waipio_cdp_pinout_v1.2.xlsx"

    generate_mvp = Generate_MVP(excel_pinout, chip_version)
    generate_mvp.create_mvp_file()

if __name__ == "__main__":
    main()