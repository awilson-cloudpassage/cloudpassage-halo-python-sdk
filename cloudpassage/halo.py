import base64
import json
import requests
import threading
import time
from exceptions import CloudPassageAuthentication


class HaloSession:
    """ Create a Halo API connection object.

    On instantiation, it will attempt to authenticate \
    against the Halo API using the apikey and apisecret \
    provided, together with any overrides passed in through \
    kwargs.

    Args:
        apikey (str): API key, retrieved from your CloudPassage Halo account
        apisecret (str): API key secret, found with your API key in your \
        CloudPassage Halo account

    Keyword Args:
        api_host (str): Override the API endpoint hostname. \
        Defaults to api.cloudpassage.com.
        api_port (str): Override the API HTTPS port \
        Defaults to 443.
        proxy_host (str): Hostname or IP address of proxy
        proxy_port (str): Port for proxy.  Ignored if proxy_host is not set
        user_agent (str): Override for UserAgent string.  We set this so that \
        we can see what tools are being used in the field and \
        set our development focus accordingly.  To override \
        the default, feel free to pass this kwarg in.

    """

    def __init__(self, apikey, apisecret, **kwargs):
        self.auth_endpoint = 'oauth/access_token'
        self.api_host = 'api.cloudpassage.com'
        self.api_port = 443
        self.user_agent = 'CloudPassage Halo Python SDK v1.0'
        self.key_id = apikey
        self.secret = apisecret
        self.auth_token = None
        self.auth_scope = None
        self.proxy_host = None
        self.proxy_port = None
        self.lock = threading.RLock()
        self.api_count = 0
        self.api_time = 0.0
        # Override defaults for proxy
        if "proxy_host" in kwargs:
            self.proxy_host = kwargs["proxy_host"]
            if "proxy_port" in kwargs:
                self.proxy_port = kwargs["proxy_port"]
        # Override defaults for api host and port
        if "api_host" in kwargs:
            self.api_host = kwargs["api_host"]
        if "api_port" in kwargs:
            self.api_port = kwargs["api_port"]
        if "user_agent" in kwargs:
            self.user_agent = kwargs["user_agent"]
        return None

    def build_proxy_struct(host, port):
        """This builds a structure describing the environment's HTTP
        proxy requirements.

        It returns a dictionary object that can be passed to the
        requests module.
        """

        ret_struct = {"https": ""}
        if port is not None:
            ret_struct["https"] = "http://" + str(host) + ":" + str(port)
        else:
            ret_struct["https"] = "http://" + str(host) + ":8080"
        return(ret_struct)

    def get_auth_token(self, endpoint, headers):
        """This method takes endpoint and header info, and returns the
        oauth token and scope.

        Args:
            endpoint (str): Full URL, including schema.
            headers (dict): Dictionary, containing header with encoded \
            credentials.

        Example:
            {"Authorization": str("Basic " + encoded)}
        """

        token = None
        scope = None
        resp = requests.post(endpoint, headers=headers)
        if resp.status_code == 200:
            auth_resp_json = resp.json()
            token = auth_resp_json["access_token"]
            scope = auth_resp_json["scope"]
        if resp.status_code == 401:
            token = "BAD"
        return(token, scope)

    def authenticate_client(self):
        """This method attempts to set an OAuth token

        Call this method and it will use the API key and secret
        as well as the proxy settings (if used) to authenticate
        this HaloSession instance.

        """

        success = False
        prefix = self.build_endpoint_prefix()
        endpoint = prefix + "/oauth/access_token?grant_type=client_credentials"
        combined = self.key_id + ':' + self.secret
        encoded = base64.b64encode(combined)
        headers = {"Authorization": str("Basic " + encoded)}
        max_tries = 5
        for i in range(max_tries):
            token, scope = self.get_auth_token(endpoint, headers)
            if token == "BAD":
                # Add message for IP restrictions
                exc_msg = "Invalid credentials- can not obtain session token."
                raise CloudPassageAuthentication(exc_msg)
            if token is not None:
                self.auth_token = token
                self.auth_scope = scope
                success = True
                break
            else:
                time.sleep(1)
        return(success)

    def build_endpoint_prefix(self):
        """This constructs everything to the left of the file path in the URL.

        """

        prefix = "https://" + self.api_host + ":" + str(self.api_port)
        return(prefix)

    def build_header(self):
        """This constructs the auth header, required for all API interaction.

        """

        authstring = "Bearer " + self.auth_token
        header = {"Authorization": authstring,
                  "Content-Type": "application/json",
                  "User-Agent": self.user_agent}
        return(header)
