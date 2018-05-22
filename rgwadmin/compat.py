
import urllib
try:
    quote = urllib.parse.quote
except AttributeError:
    quote = urllib.pathname2url
