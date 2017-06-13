import logging
import pprint

from raygun4py import raygunprovider

from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger(__name__)


class RaygunMiddleware(object):

    def __init__(self):
        apiKey = getattr(settings, 'RAYGUN4PY_API_KEY', None)
        self.sender = raygunprovider.RaygunSender(apiKey)

    def process_exception(self, request, exception):
        raygunRequest = self._mapRequest(request)

        # checking debug is what's different from raygun's provided middleware
        is_unittesting = settings.IS_UNIT_TESTING if hasattr(settings, 'IS_UNIT_TESTING') else False
        if settings.DEBUG or is_unittesting:
            logger.debug("Not sending error to raygun because DEBUG or IS_UNIT_TESTING. request to send = \n%s" % pprint.pformat(raygunRequest))
        else:
            self.sender.send_exception(exception=exception, request=raygunRequest)
            return HttpResponse('<h1>Server Error (500)</h1>', status=500)

    def _mapRequest(self, request):
        headers = request.META.items()
        _headers = dict()
        for k, v in headers:
            if not k.startswith('wsgi'):
                _headers[k] = v

        raw_data = None
        if hasattr(request, 'body'):
            raw_data = request.body
        elif hasattr(request, 'raw_post_data'):
            raw_data = request.raw_post_data

        return {
            'hostName': request.get_host(),
            'url': request.path,
            'httpMethod': request.method,
            'ipAddress': request.META.get('REMOTE_ADDR', '?'),
            'queryString': dict((key, request.GET[key]) for key in request.GET),
            'form': dict((key, request.POST[key]) for key in request.POST),
            'headers': _headers,
            'rawData': raw_data,
        }
