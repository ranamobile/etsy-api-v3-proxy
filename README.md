# Introduction

This mini project pulls listings from Etsy API v3 to be displayed on another website.

This projects uses an AWS Lambda function to proxy data to an embedded HTML/JS snippet to work around the CORS issue for the embedded script.

```
|-----------------|     |-----------------|     |-----------------|
|                 |     |                 |     |                 |
|   Etsy API v3   |---->|   AWS Lambda    |---->|   Google Site   |
|      REST       |     |     Python      |     |     HTML/JS     |
|                 |     |                 |     |                 |
|-----------------|     |-----------------|     |-----------------|
```

# Setup

## Generate an Oauth Access Token from Etsy API v3

Navigate to the Etsy developer portal to create a new app, and fill in information for you application.

https://www.etsy.com/developers/your-apps

In the callback URLs, add an option for http://localhost:9002 or a port of your choosing that is available on your localhost.

Copy the Etsy API Key for you application to run the etsy-oauth.py script.

```
python etsy-oauth.py --etsy_api_key YOUR_ETSY_API_KEY
```

This will generate an Oauth access token that is used to authenticate with the Etsy API endpoints.

**Note, you can use the Oauth token directly from your web server application. The remainder of this README documents how to set up a proxy for the Etsy API endpoints, specifically listings for a specified shop.**

## (Optional) Create an AWS Lambda Function

In your AWS Console, create an AWS Lambda function using Python 3.x, and copy the contents of etsy-lambda.py into the code.

In the configurations for the AWS Lambda function, add the following environment variables with your own values.

* `ETSY_CLIENT_ID` - this is the Etsy API Key for your application
* `ETSY_ACCESS_TOKEN` - this is the Oauth access token generated from the previous section
* `ETSY_REFRESH_TOKEN` - this is the Oauth refresh token generated from the previous section

Enable the Function URL for the Lambda function, and copy the URL for the embedding.

## (Optional) Create an Embedding to Display Etsy Listings

In your Google Site, create an Embed component and select Embed Code.

Copy the contents of etsy-embed.html into the component, and replace the values for the following variables.

* `etsyShopName` - name of the Etsy shop you want to display listings for
* `proxyUrl` - the Lambda Function URL from the previous section
