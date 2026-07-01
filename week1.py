import pandas as pd
from pathlib import Path

yearmonths = []
solds = []
lists = []
for year in [24, 25, 26]:
    if year == 24:
        months = range(1, 13)
    elif year == 25:
        months = range(1, 13)
    else:               # 2026
        months = range(1, 5)
    for month in months:
        yearmonths.append(f"20{year:02d}{month:02d}")

for yearmonth in yearmonths:
    listfilename = Path("CRMLSListing" + yearmonth + ".csv")
    lists.append(pd.read_csv(listfilename))

    soldfilename = Path("CRMLSSold" + yearmonth + ".csv")
    if soldfilename.exists():
        solds.append(pd.read_csv(soldfilename))
    else:
        soldfilename = Path("CRMLSSold" + yearmonth + "_filled.csv")
        solds.append(pd.read_csv(soldfilename).iloc[:, :-2]) #drop last two clumns

sold = pd.concat(solds)
print('sold before concatenation')
print(sold.shape)
list = pd.concat(lists)
print('list before concatenation')
print(list.shape)
soldfiltered = sold[sold['PropertyType'] == 'Residential']
listfiltered = list[list['PropertyType'] == 'Residential']
print('sold after concatenation')
print(soldfiltered.shape)
print('list after concatenation')
print(listfiltered.shape)

soldfiltered.to_csv('sold.csv')
listfiltered.to_csv('list.csv')