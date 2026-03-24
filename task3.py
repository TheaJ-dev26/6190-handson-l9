# import the necessary libraries.
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, avg, sum, to_timestamp, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Create a Spark session
spark = SparkSession.builder.appName("RideSharingAnalytics_3").getOrCreate()

# Define the schema for incoming JSON data
schema = StructType([
    StructField("trip_id", StringType(), True),
    StructField("driver_id", StringType(), True),
    StructField("distance_km", DoubleType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("timestamp", StringType(), True)
])

# Read streaming data from socket
init_df = (
    spark.readStream
         .format("socket")
         .option("host", "localhost")
         .option("port", 9999)
         .load()
)

# Parse JSON data into columns using the defined schema
result_df = (
    init_df
    .select(from_json(col("value"), schema).alias("data"))
    .select("data.*")
)

# Convert timestamp column to TimestampType and add a watermark
result_df = (
    result_df
    .withColumn("timestamp", to_timestamp(col("timestamp")))
    .withWatermark("timestamp", "1 minute")
)

# Perform windowed aggregation: sum of fare_amount over a 5-minute window sliding by 1 minute
windowed_df = (
    result_df
    .groupBy(
        window(col("event_time"), "5 minutes", "1 minute"),
        col("driver_id")
    )
    .agg(sum("fare_amount").alias("total_fare"))
)

# Extract window start and end times as separate columns
final_df = (
    windowed_df
    .withColumn("window_start", col("window.start"))
    .withColumn("window_end", col("window.end"))
    .drop("window")
)

# Define a function to write each batch to a CSV file with column names
def write_batch(batch_df, batch_id):
    # Save the batch DataFrame as a CSV file with headers included
    output_path = f"outputs/task_3/batch_{batch_id}"
    batch_df.write.mode("overwrite").csv(output_path, header=True)

# Use foreachBatch to apply the function to each micro-batch
query = (
    final_df
    .writeStream
    .foreachBatch(write_batch)
    .outputMode("update")
    .start()
)

query.awaitTermination()
