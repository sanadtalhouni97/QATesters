import json
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from datetime import datetime

# Configure your URLs here (Name: URL)
SiteLinks = {
    "Homepage": "https://automationpanda.com/",
    "Product Page": "https://automationpanda.com/about/",
    "Contact Page": "https://automationpanda.com/contact/"
}

# Jira configuration
JIRA_URL = "https://sanadtesting.atlassian.net/"
JIRA_EMAIL = ""
JIRA_API_TOKEN = ""
JIRA_PROJECT_KEY = "SCRUM"
RELATED_ISSUE_KEY = "SCRUM-3"  # The issue to relate to

def create_jira_bug(audit_results):
    """Create a standalone Bug issue with detailed findings"""
    today = datetime.now().strftime("%Y-%m-%d")

    # Build detailed description
    description = f"*Automated Site Audit Results - {today}*\n\n"

    for page, results in audit_results.items():
        description += f"*{page}* ({results['url']}):\n"

        if results['seo_issues']:
            description += "*SEO Issues:*\n"
            for issue in results['seo_issues']:
                description += f"- {issue}\n"

        if results['broken_links']:
            description += "*Broken Links:*\n"
            for link, status in results['broken_links']:
                description += f"- {status}: {link[:70]}\n"

        description += "\n"

    url = f"{JIRA_URL}rest/api/2/issue"
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Content-Type": "application/json"}

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": f"Site Issues {today}",
            "description": description,
            "issuetype": {"name": "Bug"},
            "labels": ["automated-audit"]
        }
    }

    try:
        # Create the bug
        response = requests.post(
            url,
            headers=headers,
            auth=auth,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        new_issue_key = response.json()["key"]
        print(f"\n✅ Created Bug: {new_issue_key}")

        # Link to related issue
        link_payload = {
            "type": {"name": "Relates"},  # Changed to a known valid link type "Blocks"
            "inwardIssue": {"key": new_issue_key},
            "outwardIssue": {"key": RELATED_ISSUE_KEY}
        }

        link_response = requests.post(
            f"{JIRA_URL}rest/api/2/issueLink",
            headers=headers,
            auth=auth,
            json=link_payload,
            timeout=10
        )

        if link_response.status_code == 201:
            print(f"🔗 Linked {new_issue_key} to {RELATED_ISSUE_KEY}")
        else:
            print(f"⚠️ Failed to create link: {link_response.text}")

        return new_issue_key

    except RequestException as e:
        print(f"\n❌ Failed to create bug: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print("Jira API Response: ", e.response.json())
        return None

def check_seo_issues(soup, base_url):
    """Check for common SEO issues"""
    issues = []

    # Meta description check
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if not meta_desc or not meta_desc.get('content'):
        issues.append('Missing meta description')
    else:
        desc_length = len(meta_desc['content'])
        if desc_length < 120:
            issues.append(f'Short meta description ({desc_length}/150 chars)')
        elif desc_length > 160:
            issues.append(f'Long meta description ({desc_length}/150 chars)')

    # Heading checks
    h1_tags = soup.find_all('h1')
    if len(h1_tags) != 1:
        issues.append(f'Found {len(h1_tags)} H1 tags (should be 1)')

    # Image alt text
    images = soup.find_all('img')
    for img in images:
        if not img.get('alt'):
            src = img.get('src', '')[:50]
            issues.append(f'Missing alt text: {src}...')

    # Canonical check
    canonical = soup.find('link', rel='canonical')
    if not canonical:
        issues.append('Missing canonical URL')
    else:
        canon_url = canonical.get('href', '')
        if not canon_url.startswith('https://'):
            issues.append(f'Non-HTTPS canonical: {canon_url[:50]}...')

    return issues

def check_broken_links(soup, base_url):
    """Check for broken links on the page"""
    broken_links = []
    links = soup.find_all('a')

    for link in links[:50]:  # Limit to first 50 links
        href = link.get('href')
        if not href or href.startswith(('mailto:', 'tel:', 'javascript:')):
            continue

        absolute_url = urljoin(base_url, href)

        try:
            response = requests.head(absolute_url, allow_redirects=True, timeout=5)
            if response.status_code >= 400:
                status = f"{response.status_code} {response.reason}"
                broken_links.append((absolute_url, status))
        except RequestException as e:
            broken_links.append((absolute_url, f"Connection error: {str(e)}"))

    return broken_links

def analyze_page(page_url, page_name):
    """Analyze the page for SEO issues and broken links"""
    audit_results = {'url': page_url, 'seo_issues': [], 'broken_links': []}

    try:
        response = requests.get(page_url, timeout=10)
        response.raise_for_status()

        # Parse the page content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check SEO issues and broken links
        seo_issues = check_seo_issues(soup, page_url)
        broken_links = check_broken_links(soup, page_url)

        # Update audit results
        if seo_issues:
            audit_results['seo_issues'] = seo_issues
        if broken_links:
            audit_results['broken_links'] = broken_links

        print(f"Audit results for {page_name} ({page_url}):")
        if audit_results['seo_issues']:
            print(f"  SEO Issues: {', '.join(audit_results['seo_issues'])}")
        if audit_results['broken_links']:
            print(f"  Broken Links: {', '.join([link[0] for link in audit_results['broken_links']])}")
        else:
            print(f"  No issues found!")

        return audit_results
    except RequestException as e:
        print(f"Failed to fetch {page_name} ({page_url}): {str(e)}")
        return None

def main():
    audit_results = {}

    # Loop through each site and analyze it
    for page_name, page_url in SiteLinks.items():
        results = analyze_page(page_url, page_name)
        if results:
            audit_results[page_name] = results

    # Now create Jira bug if there are any issues
    if audit_results:
        create_jira_bug(audit_results)
    else:
        print("No issues found to report.")

if __name__ == "__main__":
    main()
