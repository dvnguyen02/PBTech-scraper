"""
Upon checking pbtech robots.txt, PBTech does not mention anything about crawling, so we can crawl their site maps without any issues.

However there are some disallowed paths here:
User-agent: *
Disallow: /_staff/*
Disallow: /my-account/*
Disallow: /*myaccount*
Disallow: /basket/*
Disallow: /shipping/*
Disallow: /billing/*
Disallow: /confirm-order/*
Disallow: /checkout/*
Disallow: /process-order/*
Disallow: /order-complete/*
Disallow: /*basket$
Disallow: /*shipping$
Disallow: /*billing$
Disallow: /*confirm-order$
Disallow: /*checkout$
Disallow: /*process-order$
Disallow: /*order-complete$
Disallow: /pdf_soin.php*
Disallow: /cameras.php*
Disallow: /games.php*
Disallow: /xmlrpc.php*
Disallow: /extprint.php*
Disallow: /search*
Disallow: /code/*.php*
Disallow: /cdn-cgi/*


"""

import requests
from urllib.parse import urljoin, urlparse
import json
from collections import deque
from bs4 import BeautifulSoup


def getSiteMaps(
    url: str = "https://www.pbtech.com", outputFile: str = "sitemap.json"
) -> None:
    """
    pbtech.co.nz is behind Cloudflare's bot protection,
    so we have to opt for .com path instead of .co.nz, but the paths are mostly the same so it should be fine. This function will get all the paths from pbtech and save it to a json file.
    We will then use this to scrape all the products from pbtech later on.

    This function will get all the paths from pbtech and save it to a json file. We will then use this to scrape all the products from pbtech later on.
    Parameter:
    url: The URL to start crawling from. Default is "https://www.pbtech.com/".
    Returns:
    Json file containing all the paths found on the website.

    However if you want for global/au pb tech site, you can change the url to "https://www.pbtech.com/" or "https://www.pbtech.au/"
    and it will crawl the global site instead.
    """
    visitedSites = set()
    queue = deque([url])
    domain = urlparse(
        url
    ).netloc  # here we get all the paths from pbtech main home page
    routes = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # assuming there are 2000 unique routes
    while queue and len(visitedSites) < 2000:
        currentPath = queue.popleft()
        if currentPath in visitedSites:
            continue

        try:
            result = requests.get(
                currentPath, headers=headers, timeout=15
            )  # start with base time out 5s
            visitedSites.add(currentPath)
            path = urlparse(currentPath).path
            routes.add(path)

            # use bs4 to get all the paths from <a> tags
            soup = BeautifulSoup(result.text, "html.parser")
            allLinks = soup.find_all("a", href=True)
            for link in allLinks:
                href = link["href"]
                fullUrl = urljoin(currentPath, href)
                parsed = urlparse(fullUrl)
                # These are the not allowed paths that we got from their robots.txt file, will skip these
                if (
                    parsed.netloc is not None
                    and fullUrl not in visitedSites
                    and parsed.netloc == domain
                ):
                    skip = [
                        "my-account",
                        "_staff",
                        "myaccount",
                        "basket",
                        "shipping",
                        "billing",
                        "confirm-order",
                        "checkout",
                        "process-order",
                        "order-complete",
                        "*baseket$",
                        "*shipping$",
                        "*billing$",
                        "*confirm-order$",
                        "*checkout$",
                        "*process-order$",
                        "*order-complete$",
                        "pdf_soin.php",
                        "cameras.php",
                        "games.php",
                        "xmlrpc.php",
                        "extprint.php",
                        "search",
                        "code/*.php",
                        "cdn-cgi/*",
                    ]
                    for sk in skip:
                        if sk in parsed.path:
                            break
                    else:
                        queue.append(fullUrl)
        except Exception as e:
            print(f"Error: {currentPath} -> {e}")
            pass
    with open(outputFile, "w") as f:
        json.dump(sorted(routes), f, indent=4)
        print("Done")


def categorySiteMaps(
    sitemapPath: str = "sitemap.json", outputFile: str = "categorySites.json"
) -> None:
    """
    This function will filter out unessary paths and only keep the category paths.
    We will then use this to scrape all the products from pbtech later on.
    """
    with open(sitemapPath, "r") as f:
        allPaths = json.load(f)
    categoryPaths = []
    for path in allPaths:
        if path.startswith("/category/"):
            categoryPaths.append(path)
    with open(outputFile, "w") as f:
        json.dump(sorted(categoryPaths), f, indent=4)


getSiteMaps()
categorySiteMaps()
