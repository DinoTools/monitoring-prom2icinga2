#!/bin/sh
# SPDX-FileCopyrightText: PhiBo DinoTools (2025-)
# SPDX-License-Identifier: GPL-3.0-or-later

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <base-url> <path>"
    echo "base url: is the URL of the Prom2Icinga2 webservice"
    echo "host name: Is the name of the Icinga2 host object"
    exit 3
fi

FULL_URL="$1/check/$2"

response=$(curl -s -w "%{http_code}" -o /dev/stdout "$FULL_URL")

http_status="${response: -3}"
response_body="${response:0:-3}"

if [ "${http_status}" -eq 200 ]; then
    echo "$response_body" | jq empty 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Unknown - Response is not valid JSON."
        exit 3
    fi

    status=$(echo "$response_body" | jq '.status')
    output=$(echo "$response_body" | jq -r '.output')
    long_output=$(echo "$response_body" | jq -r '.long_output')

    echo "${output}"
    if [ "${long_output}" != "null" ]; then
        echo ""
        echo "${long_output}"
    fi

    exit "${status}"
else
    echo "Unknown"
    exit 3
fi
