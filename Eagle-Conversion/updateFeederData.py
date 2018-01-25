import urllib2
import sys

# The ID from a 'Anyone with the link can view' shared level spreadsheet
# This spreadsheet contains configurations for each different reel of components
spreadsheet_key = '1tvBd44DQMXGxgeOJC2_oDnJoUne16QYyvfrD_V1I7Do'

print("Pulling feeder data from the net...")
print("Sometimes this freezes. Feel free to close this window and try again.")

# This is the public spreadsheet that contains all our feeder data
# I'm too tired to use OAuth at the moment
url = 'https://docs.google.com/spreadsheet/ccc?key=' + spreadsheet_key + '&output=csv'
response = urllib2.urlopen(url)
data = response.read()

with open(sys.argv[1] + "feeders.csv", "wb") as code:
    code.write(data)

print("Feeder update complete")
