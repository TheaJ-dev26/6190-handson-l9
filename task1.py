from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Create a Spark session
spark = SparkSession.builder.appName("RideSharingAnalytics").getOrCreate()

# Define the schema for incoming JSON data
schema = StructType([
    StructField("trip_id", StringType(), True),
    StructField("driver_id", StringType(), True),
    StructField("distance_km", DoubleType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("timestamp", StringType(), True)
])

# Read streaming data from socket
init_df = (spark
    .readStream
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

# Print parsed data to the CSV files
query = (
    result_df
    .writeStream
    .format("console")
    .option("path", "task_1")
    .option("checkpointLocation", "checkpoint_csv")
    .option("header", True)
    .outputMode("append")
    .start()
)

query.awaitTermination()
