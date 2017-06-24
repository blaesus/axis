import os
import csv
os.chdir('~/Desktop')

f = open('xinwenlianbo_dump.csv')

reader = csv.reader(f, delimiter='|')

text = ''
for row in reader:
    if len(row[3]) > 10:
        row[2] = row[2].split(' ')[0]
        text += '\n' + '*' * 10 + '\n' + '\n'.join(row) + '\n'

out = open('xinwenlianbo_2010-2016.txt', 'w')
out.write(text)
out.close()
