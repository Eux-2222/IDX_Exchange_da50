import pandas as pd

sold = pd.read_csv('sold_with_rates.csv')
listings = pd.read_csv('listings_with_rates.csv')

#step 1
date_cols = [
    "CloseDate",
    "PurchaseContractDate",
    "ListingContractDate"
]
for column in date_cols:
    if column in sold.columns:
        sold[column] = pd.to_datetime(sold[column], format='%Y-%m-%d')
    if column in listings.columns:
        listings[column] = pd.to_datetime(listings[column], format='%Y-%m-%d')

# step 2
sold_droped = sold.drop(
    columns=[
        #'Unnamed: 0.2', 'Unnamed: 0.1', 'Unnamed: 0',
        'ListingKey', 'ListingId', #needs only one listing key, which is ListingKeyNumeric
        'BuyerAgentAOR', 'BuyerOfficeAOR', 'ListAgentAOR', #AOR not needed
        'OriginatingSystemName', 'OriginatingSystemSubName', # not needed
        'BuyerAgencyCompensation', 'BuyerAgencyCompensationType', #not needed
        'year_month' #duplicate
        ]
    )
listings_droped = listings.drop(
    columns=[
        #'Unnamed: 0.2', 'Unnamed: 0.1', 'Unnamed: 0',
        'PropertyType.1', 'ListAgentFirstName.1', 'ListAgentLastName.1', 'DaysOnMarket.1', 'LivingArea.1', 'Latitude.1', 'Longitude.1', 'ListPrice.1', 'BuyerOfficeName.1', 'UnparsedAddress.1', 'CloseDate.1',
        'year_month', #duplicate
        'ListingKey', 'ListingId', #needs only one listing key, which is ListingKeyNumeric
        'BuyerAgencyCompensation', 'BuyerAgencyCompensationType' #not needed
        ]
    )
# step 3
""" code used for analysis
critical = [
    "ClosePrice",
    "OriginalListPrice",
    "CloseDate",
    "ListingContractDate",
    "PurchaseContractDate",
    "LivingArea",
    "Latitude",
    "Longitude",
    "CountyOrParish",
    "City",
    "PostalCode",
]
print(sold_droped[critical].isna().sum()) 
print(listings_droped[critical].isna().sum()) #leave as is for all columns

# output

ClosePrice                  2
OriginalListPrice         757
CloseDate                   0
ListingContractDate         1
PurchaseContractDate      195
LivingArea                234
Latitude                15948
Longitude               15948
CountyOrParish              0
City                      311
PostalCode                  2
dtype: int64
ClosePrice              426918
OriginalListPrice          810
CloseDate               404735
ListingContractDate          0
PurchaseContractDate    296868
LivingArea                 579
Latitude                 80467
Longitude                80467
CountyOrParish               0
City                       587
PostalCode                  13
dtype: int64
"""
sold_cleaned = sold_droped[sold_droped['ClosePrice'].notna()] #for sold, remove closeprice nan because there is only 2 rows, leave as is for other columns
listings_cleaned = listings_droped
# step 4
numeric_columns = [
    "OriginalListPrice",
    "ListPrice",
    "ClosePrice",
    "LivingArea",
    "LotSizeAcres",
    "LotSizeArea",
    "LotSizeSquareFeet",
    "BuildingAreaTotal",
    "Latitude",
    "Longitude",
    "DaysOnMarket",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "ParkingTotal",
    "GarageSpaces",
    "Stories",
    "MainLevelBedrooms",
    "YearBuilt",
    "StreetNumberNumeric",
    "AssociationFee",
    "ListingKeyNumeric",
    "rate_30yr_fixed"
]

for column in numeric_columns:
    if column in sold_cleaned.columns:
        sold_cleaned[column] = pd.to_numeric(sold_cleaned[column])
    if column in listings_cleaned.columns:
        listings_cleaned[column] = pd.to_numeric(listings_cleaned[column])
# Step 5, remove
#Remove or flag invalid numeric values: ClosePrice <= 0, LivingArea <= 0, DaysOnMarket < 0, negative Bedrooms or Bathrooms
pairs = [
    ("ClosePrice", lambda x: x <= 0),
    ("LivingArea", lambda x: x <= 0),
    ("DaysOnMarket", lambda x: x <= 0),
    ("BedroomsTotal", lambda x: x < 0),
    ("BathroomsTotalInteger", lambda x: x < 0),
]
sold_cleaned_filtered = sold_cleaned
listings_cleaned_filtered = listings_cleaned
for column, condition in pairs:
    if column in sold_cleaned_filtered.columns:
        invalid = sold_cleaned_filtered[column].notna() & condition(sold_cleaned_filtered[column])
        print(f"{column}: removing {invalid.sum()} rows from sold")
        sold_cleaned_filtered = sold_cleaned_filtered[~invalid]
for column, condition in pairs:    
    if column in listings_cleaned_filtered.columns:
        invalid = listings_cleaned_filtered[column].notna() & condition(listings_cleaned_filtered[column])
        print(f"{column}: removing {invalid.sum()} rows from listings")
        listings_cleaned_filtered = listings_cleaned_filtered[~invalid]
#step 6
# ListingContractDate should precede PurchaseContractDate, which should precede CloseDate.
# Flag records with missing coordinates (Latitude or Longitude is null)
# Flag Latitude = 0 or Longitude = 0 (sentinel null values)
# Flag Longitude > 0 errors (California coordinates should be negative)
# Flag out-of-state or implausible coordinates, Latitude cannot exceed ± 90°, and Longitude cannot exceed ± 180°.
# listing_after_close_flag, purchase_after_close_flag,  negative_timeline_flag, null_lat_or_lon_flag, lon_geq_zero_flag, implausible_coord_flag
sold_final = sold_cleaned_filtered
listings_final = listings_cleaned_filtered
sold_final["listing_after_close_flag"] = (
    sold_final["ListingContractDate"].notna()
    & sold_final["CloseDate"].notna()
    & (sold_final["ListingContractDate"] > sold_final["CloseDate"])
)
sold_final["purchase_after_close_flag"] = (
    sold_final["PurchaseContractDate"].notna()
    & sold_final["CloseDate"].notna()
    & (sold_final["PurchaseContractDate"] > sold_final["CloseDate"])
)
sold_final["negative_timeline_flag"] = (
    sold_final["listing_after_close_flag"]
    | sold_final["purchase_after_close_flag"]
    | (
    sold_final["ListingContractDate"].notna()
    & sold_final["CloseDate"].notna()
    & (sold_final["ListingContractDate"] > sold_final["CloseDate"])
    )
)
sold_final["null_lat_or_lon_flag"] = (
    sold_final["Latitude"].isna()
    | sold_final["Longitude"].isna()
)
sold_final["lon_ge_zero_flag"] = (
    sold_final["Longitude"].notna()
    & (sold_final["Longitude"] > 0)
)
sold_final["implausible_coord_flag"] = (
    (
        sold_final["Latitude"].notna()
        & ((sold_final["Latitude"] < -90) | (sold_final["Latitude"] > 90))
    )
    |
    (
        sold_final["Longitude"].notna()
        & ((sold_final["Longitude"] < -180) | (sold_final["Longitude"] > 180))
    )
)
sold_final["ca_outside_flag"] = (
    sold_final["Latitude"].isnull()
    | sold_final["Longitude"].isnull()
    | (
        (sold_final["Latitude"] < 32)
        | (sold_final["Latitude"] > 42)
        | (sold_final["Longitude"] < -125)
        | (sold_final["Longitude"] > -114)
    )
)

listings_final["listing_after_close_flag"] = (
    listings_final["ListingContractDate"].notna()
    & listings_final["CloseDate"].notna()
    & (listings_final["ListingContractDate"] > listings_final["CloseDate"])
)
listings_final["purchase_after_close_flag"] = (
    listings_final["PurchaseContractDate"].notna()
    & listings_final["CloseDate"].notna()
    & (listings_final["PurchaseContractDate"] > listings_final["CloseDate"])
)
listings_final["negative_timeline_flag"] = (
    listings_final["listing_after_close_flag"]
    | listings_final["purchase_after_close_flag"]
    | (
    listings_final["ListingContractDate"].notna()
    & listings_final["CloseDate"].notna()
    & (listings_final["ListingContractDate"] > listings_final["CloseDate"])
    )
)
listings_final["null_lat_or_lon_flag"] = (
    listings_final["Latitude"].isna()
    | listings_final["Longitude"].isna()
)
listings_final["lon_ge_zero_flag"] = (
    listings_final["Longitude"].notna()
    & (listings_final["Longitude"] > 0)
)
listings_final["implausible_coord_flag"] = (
    (
        listings_final["Latitude"].notna()
        & ((listings_final["Latitude"] < -90) | (listings_final["Latitude"] > 90))
    )
    |
    (
        listings_final["Longitude"].notna()
        & ((listings_final["Longitude"] < -180) | (listings_final["Longitude"] > 180))
    )
)
listings_final["ca_outside_flag"] = (
    listings_final["Latitude"].isnull()
    | listings_final["Longitude"].isnull()
    | (
        (listings_final["Latitude"] < 32)
        | (listings_final["Latitude"] > 42)
        | (listings_final["Longitude"] < -125)
        | (listings_final["Longitude"] > -114)
    )
)

sold_final.to_csv('sold_week45.csv', index=False)
listings_final.to_csv('listings_week45.csv', index=False)