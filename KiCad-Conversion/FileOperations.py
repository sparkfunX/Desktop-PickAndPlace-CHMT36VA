class FileOperations:
    def open_file(self, file_name):
        self.file = open(file_name, 'w')

    def write_header(self):
		self.file.write("separated\n")
		self.file.write("FILE,Q_Panel.dpv\n")
		self.file.write("PCBFILE,Q_Panel.dpv\n")
		self.file.write("DATE,2017/12/01\n")
		self.file.write("TIME,11:54:53\n")
		self.file.write("PANELYPE,0\n")
		self.file.write("\n")
	
		self.file.write("Table,No.,ID,DeltX,DeltY,FeedRates,Note,Height,Speed,Status,SizeX,SizeY\n")

	#def add_feeder(self, feeder_ID):
		