#TO DO: Unexpressed items list can currently contain values that have saturated (-2). Fix this
#Normalized Plot Testing in nvLib_tests.py
#Split and normalize plot testing in nvLib_tests.py

import pandas as pd
import os,math,copy,datetime
import _plotDf as _plotDf
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

class plotCsv(object):
	"""Load a CSV file and set it up for plotting.

	.csv file should have the following structure (<lineN> doesn't appear in the actual file...)
	<line1> option1,		option2,			option3,			...
	<line2> sampleTitle,	measuredVal.1 name,	measuredVal2 Name, 	measureValue3 Name,	....
	<line3> sample1Name,	s1mv1,				s1mv2,				s1mv3,				...
	<line4> sample2Name,	s2mv1,				s2mv2,				s2mv3,				...

	Options
	=========================================
	For a complete list of all of the charting options run the member function plotCsv.listChartingOptions()

	Entries below the minimum detection limit
	=========================================
	(i) if the limit of detection is not known: "ND", "N/A", or 0 (without any quotation marks)
	(ii)if the limit of detection is know: < <LOD>, where <LOD> is the limit of detection (e.g. < 4.45, without the quotes)

	Entries above the maximum dection limit
	=========================================
	Write > <LOD>, where <LOD> is the upper limit of detection (e.g. '> 445.0', without the quotes)
	"""

	def __init__(self,filepath):
		"""Initialialize the plotCsv object using an existing .csv file

		Args:
			filepath (str or file): Existing .csv file.
		"""
		self._path = Path(filepath)
		self._filename = self._path.name.rsplit('.')[0]
		#Read the first line of the file on its own in order to select the charting options and split it across comma-separated entries
		with open(self._path) as fp:  
			optionList = fp.readline().rstrip('\n').split(',')
		optionList = [el for el in optionList if el] #remove the empty ('') elements from the list
		optionList = [el.split('=',maxsplit=1) for el in optionList] #Split off the items with a value assignment (OPT=VAL)
		#Sets every item without a value to true, otherwise assign it the proper value in a dict.
		#Note that we convert certain strings to their boolean values (see _strToBool), but leave other strings unchanged
		optionDict = dict([[el[0].upper().rstrip(),_plotDf._strToBool(el[1])] if len(el)==2 else [el[0].upper().rstrip(),True] for el in optionList])
		# print(f'List {optionList} dict: {optionDict}')
		self._params = optionDict
		self._setDefaultOptions()

		#Now read the read of the file as a dataframe, skipping the first line
		df = pd.read_csv(filepath,index_col=0,skiprows = 1, skipinitialspace=True, na_values=['ND','nd','N.D.','n.d.'])
		#We remove any columns that don't have a name (since the )
		df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
		
		#Note the key=lambda s:s.casefold() is required to have a case-insensitive sorted of the column names
		self.originalColumnOrder = list(df.columns)
		self.sortedColumnOrder = sorted(df.columns, key=lambda s:s.casefold())

		if self._params['ALPHABETIZE']:
			df=df.reindex(self.sortedColumnOrder, axis=1)

		[self._df,self._minVals,self._maxVals] = self._processDF(df)

	def _setDefaultOptions(self):
		self._params = _plotDf._setdefaultParams(self._params)
		#Delete below once you're sure it isn't needed

	# Process elements in the dataframe to (i) Replace strings that start with < with -1.0, and save that string self._minVals
	# (ii) Replace strings that start with > with -2.0, and save that string self._maxVals
	def _processDF(self,df):
		df.fillna(0,inplace=True) #Replace the NaN (N/A in a Luminex csv) with 0
		#Get the min/max value string for any columns that have an entry of the form "<val"/">val"
		minVals = self._getMinOrMaxValSeries(df,'<')
		maxVals = self._getMinOrMaxValSeries(df,'>')
		#Replace any < num string with -1.0
		df.replace(to_replace='<\s?\d+.?\d*',regex=True,value=-1.0,inplace=True)
		#Replace any > num string with -2.0
		df.replace(to_replace='>\s?\d+.?\d*',regex=True,value=-2.0,inplace=True)
		#Convert the df into floats
		dfNumeric = df.apply(pd.to_numeric)
		return [dfNumeric, minVals, maxVals]

	#Return all columns that contain one or more entries of the form "<selectionChar> value"
	#The return value will be a pandas Series of the form: ColumnName value
	def _getMinOrMaxValSeries(self,df,selectionChar):
		#Get a df containing only the strings that start with selectionChar (should be '<' or '>')
		dfVals = df[df.applymap(lambda x: str(x).startswith(selectionChar))]
		#Remove selectionChar from those strings
		regEx = selectionChar + '(\s?\d+.?\d*)'
		dfVals.replace(to_replace=regEx,regex=True,value=r'\1',inplace=True)
		#Replace the NaNs with 0 (only the minimum value should be left in each column, plus the 0s)
		dfVals.fillna(0,inplace=True)
		#Since NaNs are 0, the max of each column with be the minimum value string
		selValues = dfVals.apply(pd.to_numeric).max()
		return selValues

	def getRows(self):
		return self._df.index.tolist()

	def getCols(self):
		return self._df.columns.tolist()

	def _splitIntoSubDf(self,normalized=False):
		columnsPerDf = int(self._params['MAX_COLUMNS_PER_PLOT'])
		if normalized:
			normDf = self.getNormalizedDf()
			numberOfPlots = math.ceil(len(normDf.columns)/columnsPerDf)
			return [normDf[normDf.columns[i*columnsPerDf:(i+1)*columnsPerDf]] for i in range(numberOfPlots)]
		else:
			numberOfPlots = math.ceil(len(self._df.columns)/columnsPerDf)		
			return [self._df[self._df.columns[i*columnsPerDf:(i+1)*columnsPerDf]] for i in range(numberOfPlots)]

	#Save all of the parameters used to generate the plot in a comma-seperated text file
	def _saveParams(self):
		if len (self._params['SAVEFILE_TYPES']) != 0:
			today = datetime.date.today()
			fileName = f'{today:%Y%m%d} {self._filename}-params.txt'
			fH = open(fileName,"w")
			#Created a string from all of the parameters that are not empty strings
			outStr = ','.join([f'{el}={self._params[el]}' for el in list(self._params) if self._params[el]!=''])
			fH.write(outStr)
			fH.close()

	def _saveCurrentPlot(self,filename):
		if len (self._params['SAVEFILE_TYPES']) != 0:
			today = datetime.date.today()
			fileName = self._params['SAVEDIR'] / f'{today:%Y%m%d} {filename}'
			for ftype in self._params['SAVEFILE_TYPES']:
				plt.savefig(f'{fileName}.{ftype}',bbox_inches = 'tight')
			plt.close()

	def setParam(self,params):
		"""Set one of more plotting parameters.

		Args:
			params (dict): Key/value pairs for the plotting parameters to set.

		Parameter 		(type/default)		Description
		==================================================================================
		ALPHABETIZE		(bool/False)		Plot the measured values in alphabetical order
		LOG			(bool/False)		Plot on a logarithmic scale
		TRANSPOSE		(bool/False)		Group by sample type rather than measured items.
		HIDE_LABELS		(bool/False)		Do not label the indidual bars / heatmap patches. Overrides PRINT_ parameters
		GREYSCALE		(bool/False)		Remove color from plots
		PRINT_OOB		(bool/True)		Add N.D./SAT. labels to values below/above the detection thereshold
		PRINT_MINVAL		(bool/True)		Print the limit of detection on the bars/patches below it.
		PRINT_MAXVAL		(bool/True)		Print the limit of detection on the bars/patches below it.
		SAVEFILE_TYPES		(list/['PNG'])		Filetype(s) to save. All types supported by matplotlib can be used.  
		SAVEDIR		(Pathlib.Path/Path('.'))	Location to place the saved files. str or Path can be provided.
		NORMALIZATION_ROW	(str/'')		Row to use to normalize a plot.
		DROP_NORMALIZATION_ROW	(bool/False)		Don't include the normalization row in a normalized plot if True
		MAX_COLUMNS_PER_PLOT	(str/'9999')		Used by splitAndPlotDf() to partition a large file into multiple plots
		INCLUDE_CHARTNUMBER	(bool/False)		Used by splitAndPlotDf(). Print 'X of Y' on the split-up plots
		TITLE			(str/'')		Chart title
		XLABEL			(str/'')		X-axis label
		YLABEL			(str/'')		Y-axis label
		LEGEND_TITLE		(str/'')		Label for the legend.  Also displayed next to the color bar in a heatmap.
		"""
		for param in params:
			p = param.upper()
			if p not in self._params.keys(): 
				print(f'Invalid parameter specified: {param}')
				continue #We prevent this routine from adding new parameters
			v = params[param]

			#Ensure we don't change a Path or a list to a string 
			if isinstance(self._params[p],Path): v = Path(v) 
			if isinstance(self._params[p],list) and not isinstance(v,list): v = [v]
			self._params[p] = _plotDf._strToBool(v)
		if self._params['ALPHABETIZE']:
			self._df=self._df.reindex(self.sortedColumnOrder, axis=1)
		else:
			self._df=self._df.reindex(self.originalColumnOrder, axis=1)

	def getParam(self,param):
		"""Get the value of one plotting paracter

		Args:
			param (str): The name of the parameter to retrieve.

		Returns:
			Parameter value. Raises a KeyError if an invalid parameter is specified.
		"""
		return self._params[param.upper()]

	def plotDf(self,plotType = 'barChart',normalized=False):
		"""Charts all of the data and saves the resulting plot to a file.

		Args:
			plotType (str): The type of plot.  Currently implemented plotting types are "BARCHART" and "HEATMAP"
			normalized (bool): Whether to normalize the data relative to the sample NORMALIZATION_ROW.
				See the parameters NORMALIZATION_ROW and DROP_NORMALIZATION_ROW for more information.
		"""
		if normalized:
			plotDf = _plotDf._plotDf(df=self.getNormalizedDf(),minVals=self._minVals, maxVals=self._maxVals, params=self._params)
		else:
			plotDf = _plotDf._plotDf(plotCsvObj=self)
		if plotType.upper() == 'BARCHART':
			plotDf.barChart()
		elif plotType.upper() == 'HEATMAP':
			plotDf.heatMap()
		self._saveCurrentPlot(self._filename)

	def splitAndPlotDf(self,plotType = 'barChart',normalized=False):
		"""Split the data based on the parameter MAX_COLUMNS_PER_PLOT and plot/save subplots.

		Columns here refers to a single measured item. The number of entries per column (i.e. samples) does not
		affect the splitting.
		The value of the TRANSPOSE parameter does not affect the splitting.

		Args:
			plotType (str): The type of plot.  Currently implemented plotting types are "BARCHART" and "HEATMAP"
			normalized (bool): Whether to normalize the data relative to the sample NORMALIZATION_ROW.
				See the parameters NORMALIZATION_ROW and DROP_NORMALIZATION_ROW and the function 
				plotCsv.plotCsv.getNormalizedDf() for more information.
		"""
		subDfs = self._splitIntoSubDf(normalized)
		subPlotCsv = copy.deepcopy(self)
		for (idx,df) in enumerate(subDfs):
			subPlotCsv._df = df
			subPlotDf = _plotDf._plotDf(plotCsvObj=subPlotCsv)
			if self._params['INCLUDE_CHARTNUMBER']:
				subPlotDf._params['TITLE'] = f"{self._params['TITLE']} {idx+1} of {len(subDfs)}" 
			if plotType.upper() == 'BARCHART':
				subPlotDf.barChart()
			elif plotType.upper() == 'HEATMAP':
				subPlotDf.heatMap()
			else:
				print(f'Invalid plot type specified: {plotType}')
			self._saveCurrentPlot(f'{self._filename}-{idx+1} of {len(subDfs)}')



	#Note that we cannot normalize to rows where the normalization value is saturated
	#We should probably determine how to handle this edge case
	def getNormalizedDf(self):
		"""Normalize the data based on the NORMALIZATION_ROW parameter.

		Returns:
			pandas.DataFrame object containing the normalized data frame.  If NORMALIZATION_ROW is not in the starting
			data frame this routine returns the original data frame.
		"""

		normalizationRow = self._params['NORMALIZATION_ROW']
		if normalizationRow not in self._df.index:
			return pd.DataFrame()
		#Get the items that are expressed in the normalization row and make a data frame including only those columns
		cond1 = self._df.loc[normalizationRow]>0 
		df1 = self._df[cond1.index[cond1]]
		#Remove all of the unexpressed items from this sub data frame
		posDf = df1[df1>=0].div(df1.loc[normalizationRow])
		#The negative entries will be NaN in this DF, change them to 0
		posDf.fillna(0,inplace=True)
		negDf = df1[df1<=0].fillna(0) #Get a dataframe of the negative (unexpressed or saturated) entries
		normDf=posDf+negDf
		if self._params['DROP_NORMALIZATION_ROW']:
			return normDf.drop(normalizationRow)
		else:
			return normDf

	def getExpressedValues(self):
		"""Returns a data frame without the items that are not expressed in at least one condition."""
		unexpressed = self._df.max()<=0
		dfUnexpressed = self._df[unexpressed.index[unexpressed]]
		return self._df.drop(dfUnexpressed,axis=1)

	def getExpressedButNotNormalizable(self):
		"""Returns a list of the measured items that are not expressed in NORMALIZATION_ROW but are expressed in at least one other condition."""
		return self.getExpressedValues().drop(self.getNormalizedDf(),axis=1)

	def getUnexpressedItems(self):
		"""Returns a list of the measured items that are not expressed/below the limit of detection across all conditions."""
		unexpressed = self._df.max()<=0
		return self._df[unexpressed.index[unexpressed]].columns.tolist()
