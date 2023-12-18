const fs = require('fs');
const { Builder, By, Key, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const path = require('path');
require('chromedriver'); // This automatically sets the path

function humanLikeDelay(minDelay = 500, maxDelay = 2000) {
    return new Promise(resolve => setTimeout(resolve, Math.random() * (maxDelay - minDelay) + minDelay));
}

async function saveLocalStorage(driver, filePath) {
    let local_storage = await driver.executeScript("return JSON.stringify(localStorage);");
    if (local_storage) {
        fs.writeFileSync(filePath, local_storage);
        console.log("Local storage saved successfully.");
    } else {
        console.log("No data in local storage to save.");
    }
}

async function loadLocalStorage(driver, filePath) {
    let local_storage = fs.readFileSync(filePath, 'utf8');
    await driver.executeScript("localStorage.clear(); var data = JSON.parse(arguments[0]); for (var key in data) localStorage.setItem(key, data[key]);", local_storage);
}

async function main() {
    let driver = await new Builder().forBrowser('chrome').build();

    try {
        // Navigate to a site and interact with it before saving local storage
        await driver.get('https://www.example.com'); // Replace with the initial URL
        // ... Your interaction with the site here ...

        // Save the local storage to a file
        await saveLocalStorage(driver, 'local_storage.json');

        // Load the local storage from the file
        await loadLocalStorage(driver, 'local_storage.json');

        // Navigate to Telegram
        await driver.get('https://web.telegram.org/');
        // ... Your interaction with Telegram here ...

    } catch (error) {
        console.error('Error:', error);
    } finally {
        await driver.quit();
    }
}

main();