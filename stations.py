STATIONS = [
    {
        "name": "IRIB Radio Arabic",
        "url": "http://s0.cdn2.iranseda.ir:1935/liveedge/radio-arabic/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Avaa",
        "url": "http://s0.cdn1.iranseda.ir:1935/liveedge/radio-avaa/playlist.m3u8",
    },
    {
        "name": "IRIB Radio English",
        "url": "http://s1.cdn1.iranseda.ir:1935/liveedge/radio-english/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Farhang",
        "url": "http://s0.cdn2.iranseda.ir:1935/liveedge/radio-farhang/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Iran",
        "url": "http://s0.cdn2.iranseda.ir:1935/liveedge/radio-iran/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Javan",
        "url": "http://s0.cdn2.iranseda.ir:1935/liveedge/radio-javan/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Ma'aref",
        "url": "http://s0.cdn2.iranseda.ir:1935/liveedge/radio-maaref/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Markazi",
        "url": "http://s0.cdn1.iranseda.ir:1935/liveedgeProvincial/radio-markazi/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Namayesh",
        "url": "http://s0.cdn2.iranseda.ir:1935/liveedge/radio-namayesh/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Payam",
        "url": "http://s0.cdn1.iranseda.ir:1935/liveedge/radio-payam/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Qom",
        "url": "http://s0.cdn1.iranseda.ir:1935/liveedgeProvincial/radio-qom/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Quran",
        "url": "http://s0.cdn1.iranseda.ir:1935/liveedge/radio-quran/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Salamat",
        "url": "http://s0.cdn2.iranseda.ir:1935/liveedge/radio-salamat/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Talavat",
        "url": "http://s0.cdn1.iranseda.ir:1935/liveedge/radio-talavat/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Tartil",
        "url": "http://s0.cdn2.iranseda.ir:1935/liveedge/radio-tartil/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Varzesh",
        "url": "http://s0.cdn1.iranseda.ir:1935/liveedge/radio-varzesh/playlist.m3u8",
    },
    {
        "name": "IRIB Radio Ziarat",
        "url": "http://s0.cdn1.iranseda.ir:1935/liveedge/radio-ziarat/playlist.m3u8",
    },
    {
        "name": "IRIB TV 1",
        "url": "https://cdn-bsht1c86.telewebion.com/tv1/live/480p/index.m3u8",
    },
    {
        "name": "IRIB TV 2",
        "url": "https://cdn-bsht1c86.telewebion.com/tv2/live/480p/index.m3u8",
    },
    {
        "name": "IRIB TV 3",
        "url": "https://cdn-bsht1c86.telewebion.com/tv3/live/480p/index.m3u8",
    },
    {
        "name": "IRIB TV 4",
        "url": "https://cdn-bsht1c87.telewebion.com/tv4/live/576p/index.m3u8",
    },
    {
        "name": "IRIB TV IRINN",
        "url": "https://cdn-bsht1c82.telewebion.com/irinn/live/480p/index.m3u8",
    },
    {
        "name": "IRIB TV PRESSTV",
        "url": "https://cdnlive.presstv.ir/cdnlive/smil:cdnlive.smil/playlist.m3u8",
    },
    {
        "name": "IRIB TV Quran",
        "url": "https://cdn-bsht1c83.telewebion.com/quran/live/480p/index.m3u8",
    },
    {
        "name": "IRIB TV Salamat",
        "url": "https://cdn-bsht1c86.telewebion.com/salamat/live/576p/index.m3u8",
    },
]


def get_station_names():
    choices = []
    for item in STATIONS:
        choices.append(item["name"])
    return choices


def get_station_url(name: str):
    for item in STATIONS:
        if item["name"] == name:
            return item["url"]
    return None
