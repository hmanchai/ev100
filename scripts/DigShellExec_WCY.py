#########################################
# This version of DigshellExec.py is an #
# early version, friendly for manual    #
# test in bench.                        #
#########################################

REVISION = 'DigShellExec.py REV : 1.00.00 10/09/20'
print(REVISION)
import json
import os
import sys
# import subprocess
import pandas as pd
import fnmatch
from ev100_dlog_postprocess import dlog_csv_post_process
# from ev100_vector_conversion_lahaina import sorted_alphanumeric


## variables for user to define ##
proj = 'waipio'
#test_dir = r'F:\ATPG_CDP\Lahaina\r2\pattern_execution\SAF_120320_10pat_topoff_cgc_sr_only'
#test_dir = r'F:\demo\demo_test_022421'
test_dir = r'G:\ATPG_CDP\pattern_execution\pattern_list\SVS'
#test_dir = r'F:\ATPG_CDP\Lahaina\r2\pattern_execution\Pattern_list\042921_tdf_test\svs'
#csv_output_folder = '021121_G745board_0x826CFB17'
csv_output_folder = '061621_waipio_int_saf_svs'
summary_dlog = 'all_comp_2_run_2'
#summary_dlog = 'waipio_0x0D9BA4C6_pattern_20ns_1'
list_dirs_exclude = []
##################################

if (len(sys.argv) < 2):
    if proj == 'waipio':
        jsonfile = r"C:\vi\pats_abs\go_Waipio_abs.json"
    elif proj == 'lahaina':
        jsonfile = r"C:\vi\pats_abs\go_Lahaina_abs.json"
    else:
        raise Exception ("Error! proj is not correctly defined, please double check.")
            
else:
	jsonfile = sys.argv[1]
# tempfile = 'temp.json'
if proj == 'waipio':
    tempfile = r"C:\AXITestPrograms\DigShell\waipio_temp.json"
elif proj == 'lahaina':
    tempfile = r"C:\AXITestPrograms\DigShell\lahaina_temp.json"
    
with open(jsonfile) as f:
	data = json.load(f)
print(json.dumps(data, sort_keys=True, indent=4))


## user to modify parameters in temp json ##
freq_to_test = 0
freq_step = 0

print('modifying json.....')
data['BREAKPOINT'] = 0
data["LOOPS"] = 1
data["SERVER_LOOP"] = 0
data["RESET_AT_END"] = 2
data["FAILPINS"] = "ALL_PINS"
data["ADDER0"] = freq_step
data["ADDER1"] = freq_step
data["T0FREQ"] = freq_to_test
data["T1FREQ"] = freq_to_test
data["PATMODE"] = "ABSOLUTE"
data["SKIPLOAD"] = 0

print('done modifying json .....')
############################################

#create output dir for csv
#par_dir = r'F:\ATPG_CDP\Lahaina\r2\pattern_execution\Output'
par_dir = os.path.join(test_dir,'Output')
output_dir = os.path.join(par_dir, csv_output_folder)
if not os.path.exists(output_dir):
	try:
		os.makedirs(output_dir)
	except Exception as e:
		print(e)
	else:
		print('directory created for csv: ', output_dir)

# modify PATS.txt name and relevant directories dynamically
for root,dirs,files in os.walk(test_dir, topdown=True):
	# exclude folers
	dirs[:] = [d for d in dirs if d not in list_dirs_exclude]

	for file in files:
		if fnmatch.fnmatch(file,'PATS_*.txt'):

			par_dir = root + r'\\'
			data['PATDIR'] = par_dir
			dlog_dir = par_dir + r'\\dlog\\'
			data['DLOGDIR'] = dlog_dir
			fail_dir = par_dir + r'\\failures\\'
			data['FAILDIR'] = fail_dir

			data["PATFILE"] = os.path.basename(file)

			with open(tempfile, 'w') as write_file:
				x = json.dump(data, write_file, indent=4)
			command = r'C:\AXITestPrograms\DigShell\DigShell.exe {0}'.format(tempfile)
			print('\nCommand: ' + command)
			res = os.system(command)
			print('os.sytem execution result: ', res)

			# generate summary dlog csv
			dlog_csv_post_process(dlog_dir, output_dir, summary_dlog, file)

print('\n**** Test execution completed. Data processing in progress ****')

# post process the summary dlog
csv_output = os.path.join(output_dir, summary_dlog + '.csv')
df_summary = pd.read_csv(csv_output)

vector_cnt = df_summary.shape[0]
pass_cnt = df_summary[df_summary['Failures']==0].shape[0]
fail_cnt = vector_cnt - pass_cnt
if fail_cnt:
#print(f'{fail_cnt} out of {vector_cnt} patterns failed! This part will be placed in the fail bin.')
    print(' patterns failed! This part will be placed in the fail bin.')
else:
#print(f'All {vector_cnt} patterns passed! This part will be placed in the pass bin.' )
    print('This part will be placed in the pass bin.' )




