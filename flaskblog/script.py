from geopy.geocoders import GoogleV3

def get_latitude_longitude(address):
    try:
        geolocator = GoogleV3(api_key="AIzaSyCLYCsyffL84AgTvNV79Tp-IvAm_OcaQcE")
        location = geolocator.geocode(address)
        return location.address, location.latitude, location.longitude
    except:
        # Handle the error here. You can return a default value, log the error, or do something else.
        return address, 0, 0

