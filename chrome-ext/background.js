
    chrome.webRequest.onBeforeSendHeaders.addListener(
        function(details) {
            let found = false;
            let headers = details.requestHeaders;
            for (let i = 0; i < headers.length; ++i) {
                if (headers[i].name.toLowerCase() === 'user-agent') {
                    headers[i].value = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36';
                    found = true;
                    break;
                }
            }
            if (!found) {
                headers.push({
                    name: 'User-Agent',
                    value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
                });
            }
            return { requestHeaders: headers };
        },
        { urls: ['<all_urls>'] },
        ['blocking', 'requestHeaders']
    );

    