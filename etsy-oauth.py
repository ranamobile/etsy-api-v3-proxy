"""
This script will generate an oauth access token for accessing the Etsy API v3.

See documentation for more information on this process:

    https://developers.etsy.com/documentation/essentials/authentication
"""
import argparse
import base64
import hashlib
import http.server
import json
import secrets
import urllib.parse
import urllib.request

etsy_api_key = ""
etsy_code_verifier = ""
etsy_code_challenge = ""
etsy_code_response = ""
etsy_redirect_uri = ""
etsy_access_token = ""
etsy_refresh_token = ""


def generate_verifier(length: int):
    assert 43 < length < 130, "Code verifier length must be betwen 43 and 128"

    return secrets.token_urlsafe(96)[:length]


def generate_challenge(verifier: str):
    assert 43 < len(verifier) < 130, "Code verifier length must be between 43 and 128"

    hashed_verifier = hashlib.sha256(verifier.encode('ascii')).digest()
    encoded_verifier = base64.urlsafe_b64encode(hashed_verifier)
    return encoded_verifier.decode('ascii')[:-1]


class OauthHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        global etsy_api_key
        global etsy_code_verifier
        global etsy_code_response
        global etsy_redirect_uri

        parsed_path = urllib.parse.urlparse(self.path)
        parsed_query = urllib.parse.parse_qs(parsed_path.query)

        etsy_code_response = parsed_query.get("code", "")
        if etsy_code_response and len(etsy_code_response) > 0:
            etsy_code_response = etsy_code_response[0]

        try:
            payload = {
                "client_id": etsy_api_key,
                "code_verifier": etsy_code_verifier,
                "code": etsy_code_response,
                "grant_type": "authorization_code",
                "redirect_uri": etsy_redirect_uri,
            }
            request = urllib.request.Request(
                "https://api.etsy.com/v3/public/oauth/token",
                data=urllib.parse.urlencode(payload).encode("ascii"),
                headers={"content-type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(request) as response:
                content = json.loads(response.read())
                etsy_access_token = content.get("access_token", "")
                etsy_refresh_token = content.get("refresh_token", "")

                print(f'Access Token: {etsy_access_token}')
                print(f'Refresh Token: {etsy_refresh_token}')
                print()
                print("Copy these tokens into your lambda function")

        except:
            import traceback
            traceback.print_exc()

        super(OauthHttpRequestHandler, self).do_GET()


def main():
    global etsy_api_key
    global etsy_code_verifier
    global etsy_code_challenge
    global etsy_redirect_uri

    parser = argparse.ArgumentParser()
    parser.add_argument("--etsy_api_key",
                        default="1234567890",
                        help="Etsy API key or Client ID from the developer portal")
    parser.add_argument("--etsy_redirect_uri",
                        default="http://localhost:9002",
                        help="Redirect URI to the main page of the target app")
    parser.add_argument("--etsy_scopes",
                        nargs="*",
                        default=["listings_r", "listings_w", "shops_r", "shops_w"])
    args = parser.parse_args()

    etsy_code_verifier = generate_verifier(128)
    etsy_code_challenge = generate_challenge(etsy_code_verifier)
    etsy_redirect_uri = args.etsy_redirect_uri
    etsy_api_key = args.etsy_api_key
    scopes = " ".join(args.etsy_scopes)

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": etsy_api_key,
        "redirect_uri": etsy_redirect_uri,
        "state": "superstate",
        "code_challenge": etsy_code_challenge,
        "code_challenge_method": "S256",
        "scope": scopes,
    }, quote_via=urllib.parse.quote)
    etsy_oauth_url = f"https://www.etsy.com/oauth/connect?{params}"

    print()
    print("Click this link to authorize the application and generate an access token.")
    print()
    print(etsy_oauth_url)
    print()

    httpd = http.server.HTTPServer(('localhost', 9002), OauthHttpRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
