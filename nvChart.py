


INPUTDIR = '2019-10-11 Toleregenic vaccine charts'

import os, shutil, pathlib
from Bio import SeqIO
#The block below is required to import all of the nvLib elements
import pathlib,sys,os,math,datetime
import pandas as pd
import matplotlib.pyplot as plt
import dfProcessing, _plotDf

nvLibPath = pathlib.Path.cwd().parent.joinpath('nvLib')
if not nvLibPath.exists():
	print("ERROR: Can't locate nvLib. Expected to find it at\n\t"+str(nvLibPath))
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, str(nvLibPath))
#seqFileProcessing.py is in the nvLib folder
import novesliceElementTypeDetermination

def main():

	ROOTINPUTDIR = 'Input'
	OUTPUTDIR = 'Charts'
	DEFAULT_DIR = ''

	pathForInputData = pathlib.Path.cwd() / ROOTINPUTDIR / INPUTDIR
	pathForOutputFiles = pathlib.Path.cwd() / ROOTINPUTDIR / INPUTDIR / OUTPUTDIR
	pathForDefaultConfig = pathlib.Path.cwd() / DEFAULT_DIR / 'defaultSettings.txt'

	if not os.path.exists(pathForInputData):
		print("Can't locate input directory\n\t"+pathForInputData+"\nQuitting.")
		return

	#Get the default charting settings as well as any specific settings for the data
	defaultConfig = getHardcodedDefaults()
	defaultConfig.update(getConfigurationSettings(pathForDefaultConfig))

	#Make the output directory if it does not exist
	if not os.path.exists(pathForOutputFiles):
		print('Creating output directory\n\t'+str(pathForOutputFiles))
		os.mkdir(pathForOutputFiles)
		print('SUCCESS')
	else:
		print('Output will be stored in\n\t' + str(pathForOutputFiles))

	#Plot any csv files in the input directory
	for f in pathForInputData.glob('*.csv'):
		print('Plotting file ' + str(f.name))
		specificConfig = getConfigurationSettings(pathForInputData / 'Settings.txt')
		config = mergeConfigs(defaultConfig,specificConfig)
		import pdb;pdb.set_trace()
		plot = plotCSVfile(f,config)
		print('Saving plot')
		plt.savefig(pathForOutputFiles.joinpath(f.stem + '.jpg'),bbox_inches = 'tight')
		#plt.savefig(f'{fileName}.{ftype}',bbox_inches = 'tight')

def plotCSVfile(file,params):
	df = pd.read_csv(file,index_col=0, skipinitialspace=True, na_values=['ND','Nd','nd','N.D.','n.d.'])
	#Note the key=lambda s:s.casefold() is required to have a case-insensitive sorted of the column names
	import pdb;pdb.set_trace()
	dfProcessing.barChart(df,params)

def getConfigurationSettings(inputFile):
	returnDict = {}
	#Check for config file existance
	if not inputFile.exists():
		print('Unable to load configuration file ' + str(inputFile) + '. File not found.')
		return None
	print('loading configuration file ' + str(inputFile))
	with open(inputFile) as f:
		for line in f:
			#Remove comments and split the remaining entries on commas
			lineEntries = line.casefold().rsplit('#',maxsplit=1)[0].strip()
			if lineEntries == '': continue #Line was just a comment, so skip over processing this line
			if len(lineEntries) == 1:
				returnDict[lineEntries[0]] = True
			else:
				values = [x.strip() for x in lineEntries.split(',')]
				returnDict[lineEntries[0]] = values
	return returnDict

def mergeConfigs(config,specificConfig):
	#If there are any parameters in specificConfig that aren't listed in the default config list
	#then either (A) These parameters shouldn't exist (B) we forgot to specify defaults
	if not specificConfig: return
	unknownParameters = set(specificConfig.keys()) - set(config.keys())
	print(f'The following unknown parameters from Settings.txt are unknown and will be ignored:\n\t' \
		  f'{" ".join(str(x) for x in unknownParameters)}')
			 
	#Warn about any parameters that we'll overwrite
	overwrittenParameters = set(specificConfig.keys()).intersection(set(config.keys()))
	print(f'The following parameters from Settings.txt will overwrite the default parameters:\n\t' \
		  f'{" ".join(str(x) for x in overwrittenParameters)}')

	#update config with only the values that are in both dicts (so that we ensure we have specified defaults
	#for all of the parameters)
	config.update((k, specificConfig[k]) for k in config.keys() & specificConfig.keys())

	return convertBools(config)

def getHardcodedDefaults():
	"""
		Parameter 				Default value 	Description
		alphabetize				false			Plot the measured values in alphabetical order
		log						false			Plot on a logarithmic scale
		transpose				false			Group by sample type rather than measured items.
		hide_labels				false			Do not label the indidual bars / heatmap patches. Overrides PRINT_ parameters
		greyscale				false			Remove color from plots
		print_oob				true			Add N.D./SAT. labels to values below/above the detection thereshold
		print_minval			true			Print the limit of detection on the bars/patches below it.
		print_maxval			true			Print the limit of detection on the bars/patches below it.
		normalization_row		''				Row to use to normalize a plot.
		drop_normalizatiON_row	false			Don't include the normalization row in a normalized plot if True
		max_columns_per_plot	9999			Used by splitAndPlotDf() to partition a large file into multiple plots
		include_chartnumber		false			Used by splitAndPlotDf(). Print 'X of Y' on the split-up plots
		title					''				Chart title
		xlabel					''				X-axis label
		ylabel					''				Y-axis label
		legend_title			''				Label for the legend.  Also displayed next to the color bar in a heatmap.
	"""
	params = {
		'alphabetize': 					False,
		'log': 							False,
		'transpose': 					False,
		'hide_labels': 					False,
		'greyscale': 					False,
		'print_oob': 					True,
		'print_minval':					True,
		'print_maxval':					True,
		'normalization_row': 			'',
		'drop_normalization_row': 		False,
		'max_columns_per_plot':			'9999',	
		'include_chartnumber': 			False,	
		'title': 						'',
		'xlabel': 						'',
		'ylabel': 						'',
		'legend_title':					''
	}
	return params

def convertBools(inDict):
	for key in inDict.keys(): inDict[key]=_strToBool(inDict[key])
	return inDict


def _strToBool(inStr):
	"""
	If the input is not a string, returns the original item.
	Otherwise, turns certain strings into True/False bools, else returns the string minus any left side whitespace.
	"""
	if  np.issubdtype(type(inStr),np.number) or type(inStr) == str:
		if str(inStr).upper() in ('FALSE','NO','OFF'): return False
		elif str(inStr).upper() in ('TRUE','YES','ON'): return True
		else: return str(inStr).lstrip()
	else:
		return inStr

def getCSVfileList(directory):
	return 

if __name__ == '__main__':
	main()