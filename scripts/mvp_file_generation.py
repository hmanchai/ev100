import collections
import numbers
import os
import re
import numpy as np
import pandas as pd


class GenerateMVP:
    """
    Class to automatically generate MVP file when given excel file containing required fields
    and chip version. The file will automatically be added to common directory
    based on chip version information. Will be used to execute DigShell.
    """
    def __init__(self, excel_pinout, chip_version):
        """
        Initialize variables and set standardized formatting of excel file columns, and determine dest
        :param excel_pinout: str
            excel sheet with channel mappings and necessary info according to requirments doc
        :param chip_version: str
            capitalized chip version name ex. Waipio
        """
        self.excel_pinout = excel_pinout
        self.chip_version = chip_version
        # dest = r"C:\AxiTestPrograms\Qualcomm" + "\\'" + chip_version + r"\Common\QCOM_" + chip_version + r"_WY_v2.MVP"
        self.dest = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\MVP file generation\QCOM_Waipio_WY_v2.txt"
        self.pin_type_order = collections.OrderedDict()
        self.pin_type_order = {'Scan In': 'IN', 'Scan Out': 'OUT', 'Clocks': 'CLK', 'JTAG': 'JTAG',
                               'EV-100 Control/Sel': 'CONTROL'}
        self.connector_col_order = ['HD Pins', 'Channels (Signals)', 'Channel(DD192)']

    def excel_to_df(self):
        """
            Converts excel file to pandas DataFrame to be parse for MVP file data
            sheet_name 2 : HD Connectors sheet from workbook
            sheet_name 1 : All Required Pins sheet from workbook
            :return df_channels: pd.DataFrame
                HD Connector excel file converted to df formatted to only include main channel mapping table
            :return df_pins: pd.DataFrame
                All Required Pins excel file converted to df
        """
        df_channels = pd.read_excel(self.excel_pinout, skiprows=1, sheet_name=2)
        df_channels.dropna(how='all')
        frames = []
        col_header = []
        for i, col_order in enumerate(self.connector_col_order):
            col_header.append([col for col in df_channels.columns if col_order in col])

        col_header = np.transpose(col_header)

        for col in col_header:
            temp_df = df_channels[col]
            temp_df.set_axis(col_header[0], axis='columns', inplace=True)
            frames.append(temp_df)

        df_channels = pd.concat(frames)
        df_channels = df_channels.dropna(axis=0, how='all')

        df_channels.reset_index(drop=True, inplace=True)

        df_pins = pd.read_excel(self.excel_pinout, sheet_name=1)
        return df_channels, df_pins

    def create_mvp_file(self):
        """
        generates .MVP file based on provided data
        Formats columns by applying space padding to align MVP file for readability
        """
        df_channels, df_pins = self.excel_to_df()
        txt_file = open(self.dest, "w")
        txt_file.write("1 Site(s)\n")
        txt_file.close()
        txt_file = open(self.dest, "a")
        # add header columns and space after
        column_header_order = ['MVP       ', 'Pin Name', 'Chassis', 'Slot', 'Channel', 'Site', 'Pattern#',
                               'Instrument Type']
        column_headers = pd.DataFrame(columns=column_header_order)
        column_headers.to_csv(self.dest, index=False, sep='\t', mode='a')
        txt_file.write("\n")
        txt_file.close()
        txt_file = open(self.dest, "a")
        temp_df = pd.DataFrame(columns=column_header_order)
        # add channels
        all_pins_df = pd.DataFrame(columns=['MVP       ', 'Pin Name'])
        temp_df, all_pins_df = self.add_channel_rows(df_channels, temp_df, all_pins_df)

        # add all pins, scan in, scan out, clk, jtag, control
        frames = [temp_df, all_pins_df]
        mvp_df = pd.concat(frames)
        mvp_df = self.add_pin_groups(df_pins, mvp_df)
        # txt_file.write(temp_df.to_string)

        mvp_df.to_csv(self.dest, index=False, sep='\t', header=False, mode='a')
        txt_file.close()

        # convert txt to mvp
        base = os.path.splitext(self.dest)[0]
        mvp_filepath = base + '.MVP'
        if os.path.exists(mvp_filepath):
            os.remove(mvp_filepath)
        os.rename(self.dest, base + '.MVP')
        print("Successfully generate MVP file")

    def add_pin_groups(self, df_pins, mvp_df):
        """
        Will add all pins, scan in, scan out, clk, jtag, control categories and corresponding gpios
        to mvp_df

        :param df_pins: DataFrame
            All Required Pins df includes info on pin organization within all pins,
            scan in, scan out, clk, jtag, control categories
        :param mvp_df: DataFrame
            DF that has initial channel layout values and will have pin category
            organizations information listed after per required MVP file format
        :return mvp_df: DataFrame
            mvp_df should have entire information needed to be converted to .MVP file with proper
            space padding formatted and columns organized
        """
        mvp_spacing = 'MVP       '
        pin_name = 'Pin Name'
        for pin_type in self.pin_type_order:
            gpio_column = df_pins.columns.get_loc(pin_type)
            type_column = gpio_column + 1
            sub_df = df_pins.iloc[1:, gpio_column: type_column + 1]
            sub_df = sub_df.dropna(how='all')
            sub_df.set_axis([pin_name, mvp_spacing], axis='columns', inplace=True)
            sub_df = sub_df[[mvp_spacing, pin_name]]
            sub_df[mvp_spacing] = sub_df[mvp_spacing].apply(lambda x: self.pin_type_order.get(pin_type))
            sub_df[mvp_spacing] = sub_df[mvp_spacing].apply(lambda x: "{:<15}".format(x))
            sub_df[pin_name] = sub_df[pin_name].apply(lambda x: x.lower())
            sub_df[pin_name] = sub_df[pin_name].apply(lambda x: self.mode_correction(x))
            sub_df[pin_name] = sub_df[pin_name].apply(lambda x: "{:<15}".format(x))
            frames = [mvp_df, sub_df]
            mvp_df = pd.concat(frames)
        return mvp_df

    def add_channel_rows(self, df_channels, mvp_df, all_pins_df):
        """
        Looks for specific regex expressions to parse channel mapping information for all pins found in
        the df_channel dataframe. Add new rows to mvp_df with correct formatting for when converted to .MVP file

        :param df_channels DataFrame
            HD Connector excel file converted to df formatted to only include main channel mapping table
        :param mvp_df: DataFrame
            DataFrame to contain ['MVP       ', 'Pin Name', 'Chassis', 'Slot', 'Channel',
            'Site', 'Pattern#','Instrument Type'] as column headers
        :param all_pins_df: DataFrame
            this dataframe is created to maximize efficiency to store information needed for ALL_PINS section
            of MVP file to be added after.
        :return mvp_df: DataFrame
            files in all pin channel mapping etc. information under correct column header.
        :return all_pins_df: DataFrame
            this dataframe is created to maximize efficiency to store information needed for ALL_PINS section
            of MVP file to be added after. ALL_PINS needs list of all pin names which is already being
            used to generate the first section mvp_df
        """
        for i, row in df_channels.iterrows():
            if not pd.isnull(row[self.connector_col_order[0]]):
                if isinstance(row[self.connector_col_order[0]], numbers.Number):
                    gpio_regex = "(GPIO)(\()(.*)(\))"
                    ev_100_regex = "(EV100_)(.*)"
                    mvp_df, all_pins_df = self.get_channel_name(mvp_df, row, gpio_regex, all_pins_df)
                    mvp_df, all_pins_df = self.get_channel_name(mvp_df, row, ev_100_regex, all_pins_df)
            else:
                continue
        return mvp_df, all_pins_df

    def get_channel_name(self, mvp_df, row, regex, all_pins_df):
        """
        Adds ['MVP       ', 'Pin Name', 'Chassis', 'Slot', 'Channel', 'Site', 'Pattern#','Instrument Type'] and
        ALL_PINS and Pin Name to respective dataframe

        :param mvp_df: DataFrame
            main dataframe that is holding MVP file information that will be converted into the .MVP file
        :param row: DataFrame row
            individual row of channel mapping table [HD Pins, Channels (Signals), Channel(DD192),
            HD Pins, Channels (Signals), Channel(DD192), HD Pins, Channels (Signals), Channel(DD192)]
        :param regex: string
            regex expression to either apply to GPIO() or EV100_ pin naming convention that allows information
            to be parsed correctly and put into correct format for MVP file
        :param all_pins_df: DataFrame
            Dataframe that simultaneously gathers information needed for ALL_PINS (list of all pin names) while
            code is building first part of mvp files

        :return mvp_df: DataFrame
            files in all pin channel mapping etc. information under correct column header.
        :return all_pins_df: DataFrame
            this dataframe is created to maximize efficiency to store information needed for ALL_PINS section
            of MVP file to be added after.
        """
        if re.search(regex, row[self.connector_col_order[1]]):
            if "(GPIO)(\()(.*)(\))" in regex:
                pin = re.search(regex, row[self.connector_col_order[1]]).group(3)
                pin_name = 'gpio_' + pin
            else:
                pin = re.search(regex, row[self.connector_col_order[1]]).group(2)
                pin_name = pin.lower()
                pin_name = self.mode_correction(pin_name)
                pin_name = self.jtag_correction(pin_name)

            channel_num = int(row[self.connector_col_order[2]])
            pin_name = "{:<15}".format(pin_name)
            new_row = {'MVP       ': pin_name, 'Pin Name': pin_name, 'Chassis': 'A', 'Slot': '2',
                       'Channel': channel_num,
                       'Site': '1', 'Pattern#': '1', 'Instrument Type': '        Digital'}
            mvp_df = mvp_df.append(new_row, ignore_index=True)
            all_pins = 'ALL_PINS'
            all_pins = "{:<15}".format(all_pins)
            all_pins_row = {'MVP       ': all_pins, 'Pin Name': pin_name}
            all_pins_df = all_pins_df.append(all_pins_row, ignore_index=True)
        return mvp_df, all_pins_df

    def mode_correction(self, pin_name):
        """
        specifically fixes mode_0, mode_1 naming discrepancy
        Can remove method once file generated up to naming convention standard

        :param pin_name: str
            correction to pin naming convention difference between excel info and MVP file naming requirement

        :return pin_name: str
            updated pin_name according to naming convention
        """
        if re.search("(mode)(.*)", pin_name):
            if re.search("(_)", pin_name) is None:
                pin_name = 'mode' + '_' + re.search("(mode)(.*)", pin_name).group(2)
        return pin_name

    def jtag_correction(self, pin_name):
        """
        specifically fixes jtag_ naming discrepancy
        Can remove method once file generated up to naming convention standard

        :param pin_name: str
            correction to pin naming convention difference between excel info and MVP file naming requirement

        :return pin_name: str
            updated pin_name according to naming convention
        """
        if re.search("(jtag_)(.*)", pin_name):
            if re.search("(jtag_sel)", pin_name) is None:
                pin_name = re.search("(jtag_)(.*)", pin_name).group(2)
        return pin_name


def main():
    """
    input chip_version with first letter capitalized
    input excel pinout workbook with: Extra Pins Explanation, All Required Pins, HD Connectors
    """
    chip_version = 'Waipio'
    # #dest = r"C:\AxiTestPrograms\Qualcomm" + "\\'" + chip_version + r"\Common\QCOM_" + chip_version + r"_WY_v2.MVP"
    # dest = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Desktop\MVP file generation\QCOM_Waipio_WY_v2.txt"
    excel_pinout = r"C:\Users\rpenmatc\OneDrive - Qualcomm\Documents\waipio_cdp_pinout_v1.2.xlsx"

    generate_mvp = GenerateMVP(excel_pinout, chip_version)
    generate_mvp.create_mvp_file()


if __name__ == "__main__":
    main()
