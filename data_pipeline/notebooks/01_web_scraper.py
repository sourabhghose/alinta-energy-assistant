# Databricks notebook source
# MAGIC %md
# MAGIC # Alinta Energy Web Scraper
# MAGIC
# MAGIC This notebook scrapes content from alintaenergy.com.au and stores it in Bronze Delta table.
# MAGIC
# MAGIC **Schedule**: Daily at 2 AM
# MAGIC **Output**: main.sgh.bronze_scraped_content

# COMMAND ----------

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from typing import Dict, List
import time
from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Target URLs - Key sections of Alinta Energy website
BASE_URLS = [
    'https://www.alintaenergy.com.au/plans',
    'https://www.alintaenergy.com.au/plans/electricity',
    'https://www.alintaenergy.com.au/plans/gas',
    'https://www.alintaenergy.com.au/help',
    'https://www.alintaenergy.com.au/help/billing',
    'https://www.alintaenergy.com.au/help/payments',
    'https://www.alintaenergy.com.au/help/moving-house',
    'https://www.alintaenergy.com.au/solar',
    'https://www.alintaenergy.com.au/hardship',
    'https://www.alintaenergy.com.au/contact'
]

# User agent to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scraping Functions

# COMMAND ----------

def scrape_alinta_page(url: str) -> Dict:
    """
    Scrape a single page from Alinta Energy website.

    Args:
        url: Page URL to scrape

    Returns:
        Dictionary with page metadata and content
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Extract main content (try multiple selectors)
        content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_='content') or
            soup.find('body')
        )

        # Extract title
        title = ''
        if soup.find('h1'):
            title = soup.find('h1').text.strip()
        elif soup.find('title'):
            title = soup.find('title').text.strip()

        return {
            'url': url,
            'title': title,
            'content': content.get_text(separator='\n', strip=True) if content else '',
            'html': str(content) if content else '',
            'scraped_at': datetime.now().isoformat(),
            'status': 'success',
            'error': None
        }

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return {
            'url': url,
            'title': '',
            'content': '',
            'html': '',
            'scraped_at': datetime.now().isoformat(),
            'status': 'failed',
            'error': str(e)
        }

# COMMAND ----------

def scrape_all_pages(urls: List[str], delay: float = 2.0) -> List[Dict]:
    """
    Scrape multiple pages with delay between requests.

    Args:
        urls: List of URLs to scrape
        delay: Delay in seconds between requests (to be polite)

    Returns:
        List of scraped page dictionaries
    """
    results = []

    for i, url in enumerate(urls):
        print(f"Scraping ({i+1}/{len(urls)}): {url}")

        result = scrape_alinta_page(url)
        results.append(result)

        # Be polite - add delay between requests
        if i < len(urls) - 1:
            time.sleep(delay)

    return results

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute Scraping

# COMMAND ----------

print(f"Starting scrape of {len(BASE_URLS)} pages at {datetime.now()}")
print("=" * 80)

scraped_data = scrape_all_pages(BASE_URLS)

# Summary statistics
successful = sum(1 for d in scraped_data if d['status'] == 'success')
failed = sum(1 for d in scraped_data if d['status'] == 'failed')

print("=" * 80)
print(f"Scraping complete!")
print(f"  Successful: {successful}")
print(f"  Failed: {failed}")
print(f"  Total: {len(scraped_data)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save to Delta Lake (Bronze)

# COMMAND ----------

# Create DataFrame from scraped data
df = spark.createDataFrame(scraped_data)

# Display sample
print("Sample of scraped data:")
df.select("url", "title", "status").show(truncate=False)

# Write to Bronze table (append mode for incremental updates)
(df
 .write
 .format("delta")
 .mode("append")
 .option("mergeSchema", "true")
 .saveAsTable("main.sgh.bronze_scraped_content"))

print(f"\nData saved to main.sgh.bronze_scraped_content")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Verify data was written
bronze_df = spark.table("main.sgh.bronze_scraped_content")
print(f"Total records in Bronze table: {bronze_df.count()}")

# Show latest scrape
latest = bronze_df.orderBy(F.col("scraped_at").desc()).limit(5)
latest.select("url", "title", "scraped_at", "status").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cleanup
# MAGIC
# MAGIC To deduplicate data (keep only latest version of each URL):

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Deduplicate - keep only the latest scrape for each URL
windowSpec = Window.partitionBy("url").orderBy(F.col("scraped_at").desc())

deduplicated_df = (
    bronze_df
    .withColumn("row_num", F.row_number().over(windowSpec))
    .filter(F.col("row_num") == 1)
    .drop("row_num")
)

print(f"Records before deduplication: {bronze_df.count()}")
print(f"Records after deduplication: {deduplicated_df.count()}")

# Overwrite with deduplicated data
(deduplicated_df
 .write
 .format("delta")
 .mode("overwrite")
 .saveAsTable("main.sgh.bronze_scraped_content"))

print("Deduplication complete!")
