# Databricks notebook source
# MAGIC %md
# MAGIC # Process Bronze to Silver
# MAGIC
# MAGIC This notebook cleans and processes raw HTML content from Bronze layer to Silver layer.
# MAGIC
# MAGIC **Input**: main.alinta.bronze_scraped_content
# MAGIC **Output**: main.alinta.silver_clean_content

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from bs4 import BeautifulSoup
import re

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Cleaning Functions

# COMMAND ----------

def clean_html_content(html_str: str) -> str:
    """
    Extract clean text from HTML string.

    Args:
        html_str: HTML content

    Returns:
        Clean text with proper spacing
    """
    if not html_str:
        return ""

    try:
        soup = BeautifulSoup(html_str, 'html.parser')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript']):
            element.decompose()

        # Get text with proper spacing
        text = soup.get_text(separator=' ', strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    except Exception as e:
        print(f"Error cleaning HTML: {str(e)}")
        return ""

# Register UDF
clean_html_udf = F.udf(clean_html_content, StringType())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Bronze Data

# COMMAND ----------

# Read from Bronze table (only successful scrapes)
bronze_df = (
    spark.table("main.alinta.bronze_scraped_content")
    .filter(F.col("status") == "success")
    .filter(F.length("html") > 0)
)

print(f"Bronze records to process: {bronze_df.count()}")
bronze_df.select("url", "title", "scraped_at").show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Clean and Transform Data

# COMMAND ----------

# Apply cleaning transformations
silver_df = (
    bronze_df
    .select(
        F.col("url"),
        F.col("title"),
        clean_html_udf(F.col("html")).alias("clean_content"),
        F.col("scraped_at")
    )
    # Add metadata columns
    .withColumn("processed_at", F.current_timestamp())
    .withColumn("content_length", F.length("clean_content"))
    # Filter out pages with insufficient content
    .filter(F.col("content_length") >= 100)
    # Extract domain/section from URL
    .withColumn("section",
                F.when(F.col("url").contains("/plans"), "plans")
                .when(F.col("url").contains("/help"), "help")
                .when(F.col("url").contains("/solar"), "solar")
                .when(F.col("url").contains("/hardship"), "hardship")
                .otherwise("general"))
)

print(f"Silver records after cleaning: {silver_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Quality Checks

# COMMAND ----------

# Show statistics
print("Content length statistics:")
silver_df.select("content_length").describe().show()

print("\nRecords by section:")
silver_df.groupBy("section").count().orderBy("count", ascending=False).show()

print("\nSample cleaned content:")
silver_df.select("url", "title", F.substring("clean_content", 1, 200).alias("preview")).show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save to Silver Table

# COMMAND ----------

# Write to Silver table (overwrite to ensure clean state)
(silver_df
 .write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable("main.alinta.silver_clean_content"))

print("Data saved to main.alinta.silver_clean_content")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Verify Silver table
silver_table = spark.table("main.alinta.silver_clean_content")

print(f"Total records in Silver table: {silver_table.count()}")
print("\nTable schema:")
silver_table.printSchema()

print("\nSample records:")
silver_table.select("url", "title", "section", "content_length").show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Report

# COMMAND ----------

from pyspark.sql import functions as F

quality_report = silver_table.agg(
    F.count("*").alias("total_records"),
    F.countDistinct("url").alias("unique_urls"),
    F.avg("content_length").alias("avg_content_length"),
    F.min("content_length").alias("min_content_length"),
    F.max("content_length").alias("max_content_length")
)

print("Silver Layer Quality Report:")
print("=" * 80)
quality_report.show(truncate=False)

print("\nSection Distribution:")
silver_table.groupBy("section").agg(
    F.count("*").alias("count"),
    F.avg("content_length").alias("avg_length")
).orderBy("count", ascending=False).show()
