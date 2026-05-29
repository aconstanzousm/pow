from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.renderers import JSONRenderer


class ForceJSONContentNegotiation(DefaultContentNegotiation):
    def select_renderer(self, request, renderers, format_suffix=None):
        for r in renderers:
            if isinstance(r, JSONRenderer):
                return r, r.media_type
        return super().select_renderer(request, renderers, format_suffix=format_suffix)

