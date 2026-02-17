# Databricks notebook source
# MAGIC %md
# MAGIC # Create Content Chunks (Gold Layer)
# MAGIC
# MAGIC This notebook chunks clean content for vector search indexing.
# MAGIC
# MAGIC **Input**: main.alinta.silver_clean_content
# MAGIC **Output**: main.alinta.gold_content_chunks

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, StringType, StructType, StructField, IntegerType
from typing import List, Tuple
import re

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chunking Configuration

# COMMAND ----------

# Chunking parameters
CHUNK_SIZE = 400  # words per chunk
OVERLAP_SIZE = 50  # words overlap between chunks
MIN_CHUNK_SIZE = 50  # minimum words to keep a chunk

print(f"Chunking Configuration:")
print(f"  Chunk Size: {CHUNK_SIZE} words")
print(f"  Overlap: {OVERLAP_SIZE} words")
print(f"  Minimum: {MIN_CHUNK_SIZE} words")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Chunking Function

# COMMAND ----------

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP_SIZE) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Input text to chunk
        chunk_size: Target size in words
        overlap: Overlap size in words

    Returns:
        List of text chunks
    """
    if not text or len(text.strip()) == 0:
        return []

    # Split into words (simple tokenization)
    words = text.split()

    if len(words) <= chunk_size:
        return [text] if len(words) >= MIN_CHUNK_SIZE else []

    chunks = []
    start_idx = 0

    while start_idx < len(words):
        # Get chunk
        end_idx = start_idx + chunk_size
        chunk_words = words[start_idx:end_idx]

        # Only add if meets minimum size
        if len(chunk_words) >= MIN_CHUNK_SIZE:
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)

        # Move to next chunk with overlap
        start_idx += (chunk_size - overlap)

        # Break if we're at the end
        if end_idx >= len(words):
            break

    return chunks

# Register UDF
chunk_text_udf = F.udf(chunk_text, ArrayType(StringType()))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Silver Data

# COMMAND ----------

silver_df = spark.table("main.alinta.silver_clean_content")

print(f"Silver records to chunk: {silver_df.count()}")
silver_df.select("url", "title", "content_length").show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Chunks

# COMMAND ----------

# Create chunks with metadata
chunks_df = (
    silver_df
    .select(
        F.col("url"),
        F.col("title"),
        F.col("section"),
        F.col("clean_content"),
        chunk_text_udf(F.col("clean_content")).alias("chunks")
    )
    # Explode chunks array into separate rows
    .select(
        F.col("url"),
        F.col("title"),
        F.col("section"),
        F.posexplode("chunks").alias("chunk_index", "chunk_text")
    )
    # Add unique chunk ID
    .withColumn("chunk_id", F.concat_ws("_", F.col("url"), F.col("chunk_index")))
    # Add metadata
    .withColumn("chunk_length", F.length("chunk_text"))
    .withColumn("created_at", F.current_timestamp())
    # Reorder columns
    .select(
        "chunk_id",
        "url",
        "title",
        "section",
        "chunk_text",
        "chunk_index",
        "chunk_length",
        "created_at"
    )
)

print(f"Total chunks created: {chunks_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Quality Checks

# COMMAND ----------

# Chunk statistics
print("Chunk Statistics:")
chunks_df.select("chunk_length").describe().show()

print("\nChunks by section:")
chunks_df.groupBy("section").count().orderBy("count", ascending=False).show()

print("\nChunks per document:")
chunks_per_doc = (
    chunks_df
    .groupBy("url", "title")
    .agg(F.count("*").alias("num_chunks"))
    .orderBy("num_chunks", ascending=False)
)
chunks_per_doc.show(10, truncate=False)

print("\nSample chunks:")
chunks_df.select("chunk_id", "title", "chunk_index", F.substring("chunk_text", 1, 150).alias("preview")).show(3, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Save to Gold Table

# COMMAND ----------

# Write to Gold table
(chunks_df
 .write
 .format("delta")
 .mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable("main.alinta.gold_content_chunks"))

print("Data saved to main.alinta.gold_content_chunks")

# Enable Change Data Feed for Delta Sync
spark.sql("""
    ALTER TABLE main.alinta.gold_content_chunks
    SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
""")

print("Change Data Feed enabled for Vector Search sync")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Verify Gold table
gold_table = spark.table("main.alinta.gold_content_chunks")

print(f"Total chunks in Gold table: {gold_table.count()}")
print("\nTable schema:")
gold_table.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Final Quality Report

# COMMAND ----------

quality_metrics = gold_table.agg(
    F.count("*").alias("total_chunks"),
    F.countDistinct("url").alias("unique_sources"),
    F.avg("chunk_length").alias("avg_chunk_length"),
    F.min("chunk_length").alias("min_chunk_length"),
    F.max("chunk_length").alias("max_chunk_length"),
    F.avg("chunk_index").alias("avg_chunks_per_doc")
)

print("Gold Layer Quality Report:")
print("=" * 80)
quality_metrics.show(truncate=False)

print("\nDistribution by section:")
gold_table.groupBy("section").agg(
    F.count("*").alias("chunk_count"),
    F.countDistinct("url").alias("doc_count"),
    F.avg("chunk_length").alias("avg_length")
).orderBy("chunk_count", ascending=False).show()

print("\n✅ Chunking complete! Ready for Vector Search indexing.")
