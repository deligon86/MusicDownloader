from kivy.network.urlrequest import UrlRequest

def got_image(req, result):
    print("Success")

def fail(req, result):
    print("Failed:", req.resp_status)


UrlRequest('https://justnaija.com/uploads/2025/09/Mashudu-Voicemail-artwork.jpeg', on_success=got_image, on_failure=fail)
