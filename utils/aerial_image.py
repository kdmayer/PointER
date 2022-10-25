import io
import os.path
import urllib.request
import urllib.parse

from config import get_google_key


def get_aerial_image_lat_lon(latitude: float,
                             longitude: float,
                             image_name: str,
                             horizontal_px: int = 512,
                             vertical_px: int = 512,
                             scale: int = 1,
                             zoom: int = 20,
                             save_directory: str = "aerial_image_examples"):
    """
    Retrieves an aerial image from bing maps centered at a given latitude
    and longitude and saves it as .png.

    The zoom level is set to 20 as default.
    """
    api_key = get_google_key()
    params = urllib.parse.urlencode(
        {"center": f"{latitude},{longitude}", "zoom": zoom,
         "size": f"{horizontal_px}x{vertical_px}", "maptype": "satellite",
         "scale": scale, "key": api_key}
    )
    maps_url = "https://maps.googleapis.com/maps/api/staticmap"
    image_url = f"{maps_url}?{params}"
    image_file = io.BytesIO(urllib.request.urlopen(image_url).read())
    image_name = str(image_name) + '.png'

    path = os.path.join(save_directory, image_name)
    with open(path, "wb") as file:
        file.write(image_file.getbuffer())