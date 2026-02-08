import os

def playFile(fileToRead):
	os.system('mpg123 ' + fileToRead + '.mp3 &')

#playFile("../resources/system/1starting")
