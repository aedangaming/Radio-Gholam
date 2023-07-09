import pygeoip

_geoip = pygeoip.GeoIP("geoip.dat")


def lookup_country_code(ipv4_address: str):
    return _geoip.country_code_by_addr(ipv4_address)
