'''
This is a small app to create a dummy lender list to be uploaded to GDI LendTrax for testing purposes

'''

import csv
import random

with open('lenderlist.csv', 'w') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(['id', 'mei', 'parent', 'child', 'shortname', 'commitment', 'vote', 'voted', 'type', 'time'])

    iterator = int(input("How many lenders do you want? (Up to 7999)"))
    x = 0
    mei = 2000 #Arbitrary
    clo = 0
    Xid = 0


    while x < iterator:
        stuff = []

        stuff.append(str(Xid))
        Xid += 1

        stuff.append(str("KY0M00" + str(mei)))
        mei += 1

        stuff.append("Fictional Bank NA")

        stuff.append(str("Fict CLO" + str(Xid)))

        stuff.append(str("FICTCLO" + str(Xid) + "ASSO"))

        balance = float(round(random.uniform(175653, 78123654),2))
        stuff.append(str(balance))

        for y in range (0, 5):
            stuff.append('')
        writer.writerow(stuff)
        x += 1
